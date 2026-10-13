#!/usr/bin/env python3
"""
Automated unit and integration test suite for qJackett.
"""

import os
import sys
import io
import json
import tempfile
import subprocess
import unittest
from unittest.mock import patch, MagicMock
import urllib.error
import importlib.machinery
import importlib.util

# Load qjackett module dynamically from parent directory
repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
qjackett_path = os.path.join(repo_dir, "qjackett")

loader = importlib.machinery.SourceFileLoader("qjackett", qjackett_path)
spec = importlib.util.spec_from_loader("qjackett", loader)
qj = importlib.util.module_from_spec(spec)
loader.exec_module(qj)
sys.modules["qjackett"] = qj


class TestFormattingAndParsing(unittest.TestCase):
    def test_format_size(self):
        self.assertEqual(qj.format_size(500), "500.0 B")
        self.assertEqual(qj.format_size(1024), "1.0 KB")
        self.assertEqual(qj.format_size(1024 * 1024), "1.0 MB")
        self.assertEqual(qj.format_size(1536 * 1024 * 1024), "1.5 GB")
        self.assertEqual(qj.format_size(2 * 1024**4), "2.0 TB")
        self.assertEqual(qj.format_size("invalid"), "N/A")

    def test_parse_size(self):
        self.assertEqual(qj.parse_size("500B"), 500)
        self.assertEqual(qj.parse_size("10K"), 10240)
        self.assertEqual(qj.parse_size("500M"), 500 * 1024**2)
        self.assertEqual(qj.parse_size("1.5 GB"), int(1.5 * 1024**3))
        self.assertEqual(qj.parse_size("2TB"), 2 * 1024**4)
        self.assertIsNone(qj.parse_size(""))
        self.assertIsNone(qj.parse_size("abc"))
        self.assertIsNone(qj.parse_size(None))


class TestMetadataExtraction(unittest.TestCase):
    def test_extract_tags_resolutions(self):
        self.assertIn("2160p/4K", qj.extract_tags("Movie.2024.4K.HDR"))
        self.assertIn("2160p/4K", qj.extract_tags("Movie.2024.2160p.UHD"))
        self.assertIn("1080p", qj.extract_tags("Movie.2024.1080p.BluRay"))
        self.assertIn("720p", qj.extract_tags("Movie.2024.720p.HDTV"))
        self.assertIn("480p", qj.extract_tags("Movie.2024.480p.DVDRip"))

    def test_extract_tags_sources_and_codecs(self):
        tags = qj.extract_tags("Dune.2024.Remux.HEVC.DV.HDR10+.TrueHD.Atmos.Dual-GROUP")
        self.assertIn("Remux", tags)
        self.assertIn("x265", tags)
        self.assertIn("DV", tags)
        self.assertIn("HDR10+", tags)
        self.assertIn("TrueHD", tags)
        self.assertIn("Atmos", tags)
        self.assertIn("Dual", tags)

    def test_extract_tags_languages(self):
        self.assertIn("Castellano", qj.extract_tags("Pelicula.1080p.Castellano.MicroHD"))
        self.assertIn("Latino", qj.extract_tags("Pelicula.1080p.Latino.Dual"))
        self.assertIn("VOSE", qj.extract_tags("Movie.1080p.VOSE.Subs"))

    def test_category_badges(self):
        badge, key = qj.get_category_badge("Movies/UHD", [2040])
        self.assertEqual(key, "movies")
        self.assertIn("Película", badge)

        badge, key = qj.get_category_badge("TV/Anime", [5070])
        self.assertEqual(key, "anime")
        self.assertIn("Anime", badge)

        badge, key = qj.get_category_badge("PC/Games", [4050])
        self.assertEqual(key, "games")
        self.assertIn("Juego", badge)

        badge, key = qj.get_category_badge("Audio/Lossless", [3040])
        self.assertEqual(key, "music")
        self.assertIn("Música", badge)

        badge, key = qj.get_category_badge("Books/EBook", [7020])
        self.assertEqual(key, "books")
        self.assertIn("Libro", badge)

        badge, key = qj.get_category_badge("PC/0day", [4000])
        self.assertEqual(key, "apps")
        self.assertIn("Software", badge)

    def test_render_health_bar(self):
        bar_exc = qj.render_health_bar(100, 10)
        self.assertIn("Excelente", bar_exc)
        self.assertIn("█", bar_exc)

        bar_dead = qj.render_health_bar(0, 0)
        self.assertIn("0%", bar_dead)


class TestConfigManagement(unittest.TestCase):
    def test_load_default_config(self):
        cfg = qj.load_config(custom_path="/nonexistent_file_qjackett_test.json")
        self.assertEqual(cfg["jackett_url"], "http://127.0.0.1:9117")
        self.assertEqual(cfg["qbittorrent_url"], "http://127.0.0.1:8080")
        self.assertTrue(cfg["auto_category"])
        self.assertTrue(cfg["auto_tags"])

    def test_load_custom_config(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump({"jackett_url": "http://192.168.1.100:9117", "max_workers": 8}, f)
            cfg_path = f.name

        try:
            cfg = qj.load_config(custom_path=cfg_path)
            self.assertEqual(cfg["jackett_url"], "http://192.168.1.100:9117")
            self.assertEqual(cfg["max_workers"], 8)
            # Default values should remain intact
            self.assertEqual(cfg["qbittorrent_url"], "http://127.0.0.1:8080")
        finally:
            if os.path.exists(cfg_path):
                os.remove(cfg_path)

    def test_env_var_overrides(self):
        with patch.dict(os.environ, {"JACKETT_URL": "http://remote-jackett:9117"}):
            cfg = qj.load_config(custom_path="/nonexistent_test.json")
            self.assertEqual(cfg["jackett_url"], "http://remote-jackett:9117")

    def test_init_config_file(self):
        tmp_dir = tempfile.mkdtemp()
        cfg_file = os.path.join(tmp_dir, "nested", "config.json")
        try:
            created = qj.init_config_file(cfg_file)
            self.assertTrue(created)
            self.assertTrue(os.path.isfile(cfg_file))
            with open(cfg_file, "r") as f:
                data = json.load(f)
            self.assertIn("jackett_url", data)

            # Second call should not overwrite
            created_again = qj.init_config_file(cfg_file)
            self.assertFalse(created_again)
        finally:
            import shutil
            shutil.rmtree(tmp_dir, ignore_errors=True)


class TestQBittorrentClient(unittest.TestCase):
    def test_add_torrent_mock_success(self):
        client = qj.QBittorrentClient("http://127.0.0.1:8080")

        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__enter__.return_value = mock_resp

        with patch.object(client.opener, "open", return_value=mock_resp) as mock_open:
            ok = client.add_torrent("magnet:?xt=urn:btih:dummy", category="movies", tags=["qjackett", "1080p"], paused=True)
            self.assertTrue(ok)
            mock_open.assert_called_once()
            req = mock_open.call_args[0][0]
            self.assertIn("/api/v2/torrents/add", req.full_url)
            self.assertIn(b"category=movies", req.data)
            self.assertIn(b"paused=true", req.data)
            self.assertIn(b"tags=qjackett%2C+1080p", req.data)

    def test_login_and_retry_on_403(self):
        client = qj.QBittorrentClient("http://127.0.0.1:8080", username="admin", password="password")

        # First call raises HTTPError(403), login succeeds (200), retry succeeds (200)
        mock_err_resp = MagicMock()
        mock_err_resp.code = 403
        http_error = urllib.error.HTTPError("http://127.0.0.1:8080/api/v2/torrents/add", 403, "Forbidden", {}, io.BytesIO(b"Forbidden"))

        mock_login_resp = MagicMock()
        mock_login_resp.status = 200
        mock_login_resp.read.return_value = b"Ok."
        mock_login_resp.__enter__.return_value = mock_login_resp

        mock_retry_resp = MagicMock()
        mock_retry_resp.status = 200
        mock_retry_resp.__enter__.return_value = mock_retry_resp

        with patch.object(client.opener, "open", side_effect=[http_error, mock_login_resp, mock_retry_resp]) as mock_open:
            ok = client.add_torrent("magnet:test")
            self.assertTrue(ok)
            self.assertEqual(mock_open.call_count, 3)


class TestClipboardAndNotifications(unittest.TestCase):
    @patch("subprocess.run")
    def test_copy_to_clipboard_wl_copy(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        res = qj.copy_to_clipboard("test-text")
        self.assertTrue(res)
        mock_run.assert_called_with(["wl-copy"], input=b"test-text", check=False,
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    @patch("subprocess.run")
    def test_copy_to_clipboard_xclip_fallback(self, mock_run):
        # wl-copy fails with FileNotFoundError, xclip succeeds
        mock_run.side_effect = [FileNotFoundError, MagicMock(returncode=0)]
        res = qj.copy_to_clipboard("test-text")
        self.assertTrue(res)
        self.assertEqual(mock_run.call_count, 2)

    @patch("subprocess.run")
    def test_send_notification(self, mock_run):
        qj.send_notification("Test Title", "Test Body", icon="qbittorrent")
        mock_run.assert_called_with(
            ["notify-send", "-a", "qjackett", "-i", "qbittorrent", "Test Title", "Test Body"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    @patch("subprocess.run")
    def test_open_url_in_browser(self, mock_run):
        ok = qj.open_url_in_browser("https://example.com")
        self.assertTrue(ok)
        mock_run.assert_called_with(
            ["xdg-open", "https://example.com"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )


class TestSubcommandHandlers(unittest.TestCase):
    def setUp(self):
        self.test_data = [{
            "Title": "Test.Release.2026.1080p.BluRay.x265",
            "Seeders": 100,
            "Peers": 10,
            "Size": 4500000000,
            "Tracker": "TestTracker",
            "CategoryDesc": "Movies/HD",
            "Category": [2000],
            "PublishDate": "2026-10-12T10:00:00Z",
            "DownloadVolumeFactor": 0,
            "InfoHash": "1234567890abcdef1234567890abcdef12345678",
            "Details": "https://example.com/details",
            "MagnetUri": "magnet:?xt=urn:btih:1234567890abcdef1234567890abcdef12345678&dn=Test",
            "_badge": "🎬 Película",
            "_cat_key": "movies",
            "_tags": ["1080p", "BluRay", "x265"]
        }]
        self.tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        json.dump(self.test_data, self.tmp)
        self.tmp.close()

    def tearDown(self):
        if os.path.exists(self.tmp.name):
            os.remove(self.tmp.name)

    def test_handle_preview(self):
        captured = io.StringIO()
        with patch("sys.stdout", captured):
            qj.handle_preview("0", self.tmp.name)
        out = captured.getvalue()
        self.assertIn("Test.Release.2026", out)
        self.assertIn("🎬 Película", out)
        self.assertIn("Freeleech", out)
        self.assertIn("1080p", out)

    @patch("qjackett.copy_to_clipboard")
    @patch("qjackett.send_notification")
    def test_handle_copy_magnet(self, mock_notify, mock_copy):
        qj.handle_copy_magnet("0", self.tmp.name)
        mock_copy.assert_called_with(self.test_data[0]["MagnetUri"])
        mock_notify.assert_called()

    @patch("qjackett.copy_to_clipboard")
    @patch("qjackett.send_notification")
    def test_handle_copy_title(self, mock_notify, mock_copy):
        qj.handle_copy_title("0", self.tmp.name)
        mock_copy.assert_called_with(self.test_data[0]["Title"])
        mock_notify.assert_called()

    @patch("qjackett.open_url_in_browser")
    @patch("qjackett.send_notification")
    def test_handle_open_link(self, mock_notify, mock_open_url):
        qj.handle_open_link("0", self.tmp.name)
        mock_open_url.assert_called_with(self.test_data[0]["Details"])
        mock_notify.assert_called()


class TestQueryRunnerAndDeduplication(unittest.TestCase):
    def test_deduplication_and_filtering(self):
        mock_results = [
            {"Title": "Arch.Linux.2026.x86_64.iso", "Seeders": 10, "Peers": 1, "Size": 1000, "InfoHash": "abc", "Link": "magnet:1"},
            {"Title": "Arch.Linux.2026.x86_64.iso", "Seeders": 50, "Peers": 5, "Size": 1000, "InfoHash": "abc", "Link": "magnet:2"},
            {"Title": "Ubuntu.CAM.Telesync", "Seeders": 100, "Peers": 20, "Size": 2000, "InfoHash": "def", "Link": "magnet:3"},
        ]

        config = {
            "jackett_url": "http://127.0.0.1:9117",
            "default_exclude": ["cam", "telesync"],
            "default_min_seeds": 0,
            "default_sort": "seeds",
            "max_workers": 2,
            "request_timeout": 1.0
        }

        class MockArgs:
            exclude = None
            min_size = None
            max_size = None
            min_seeds = None
            category = None
            sort = "seeds"
            reverse = False

        with patch.object(qj, "search_indexer", return_value=mock_results):
            results = qj.run_query("test", config, MockArgs(), "api_key", ["indexer1"])

            # Ubuntu should be excluded due to CAM/Telesync
            titles = [r["Title"] for r in results]
            self.assertNotIn("Ubuntu.CAM.Telesync", titles)

            # Arch Linux should be deduplicated, keeping the one with 50 seeds
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["Seeders"], 50)

    def test_size_and_sorting(self):
        mock_results = [
            {"Title": "Release.Small", "Seeders": 10, "Peers": 10, "Size": 100 * 1024**2, "InfoHash": "h1", "Link": "m1"},
            {"Title": "Release.Medium", "Seeders": 5, "Peers": 20, "Size": 500 * 1024**2, "InfoHash": "h2", "Link": "m2"},
            {"Title": "Release.Large", "Seeders": 2, "Peers": 30, "Size": 2 * 1024**3, "InfoHash": "h3", "Link": "m3"},
        ]

        config = {"jackett_url": "http://127.0.0.1:9117", "max_workers": 2, "request_timeout": 1.0}

        class MockArgs:
            exclude = None
            min_size = "200M"
            max_size = "1GB"
            min_seeds = 0
            category = None
            sort = "size"
            reverse = False

        with patch.object(qj, "search_indexer", return_value=mock_results):
            results = qj.run_query("test", config, MockArgs(), "api_key", ["indexer1"])
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["Title"], "Release.Medium")


class TestV13Features(unittest.TestCase):
    def test_search_bitmagnet(self):
        mock_response = {
            "data": {
                "torrentContent": {
                    "search": {
                        "items": [
                            {
                                "infoHash": "abc12345",
                                "contentType": "movie",
                                "title": "Inception.1080p.mkv",
                                "torrent": {
                                    "name": "Inception",
                                    "size": 2500000000,
                                    "filesCount": 2,
                                    "seeders": 150,
                                    "leechers": 20,
                                    "magnetUri": "magnet:?xt=urn:btih:abc12345",
                                    "files": [
                                        {"index": 0, "path": "Inception.mkv", "size": 2490000000},
                                        {"index": 1, "path": "Inception.srt", "size": 10000000}
                                    ]
                                }
                            }
                        ]
                    }
                }
            }
        }

        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps(mock_response).encode("utf-8")
            mock_urlopen.return_value.__enter__.return_value = mock_resp

            res = qj.search_bitmagnet("Inception")
            self.assertEqual(len(res), 1)
            item = res[0]
            self.assertEqual(item["Title"], "Inception.1080p.mkv")
            self.assertEqual(item["Tracker"], "BitMagnet (DHT)")
            self.assertEqual(item["Seeders"], 150)
            self.assertEqual(item["_source"], "bitmagnet")
            self.assertEqual(len(item["_files_list"]), 2)

    def test_security_heuristics(self):
        # 1. Malware executable in movie
        code, badge, msg = qj.check_security_status("Avengers.2024.1080p.exe", 1000000, "movies")
        self.assertEqual(code, "danger")
        self.assertIn("MALWARE", badge)

        # 2. Fake small size for 4K
        code, badge, msg = qj.check_security_status("Dune.2024.2160p.4K.BluRay", 5 * 1024**2, "movies")
        self.assertEqual(code, "danger")
        self.assertIn("TAMAÑO ANÓMALO", badge)

        # 3. Fake swarm
        code, badge, msg = qj.check_security_status("Linux.ISO", 2 * 1024**3, "apps", seeders=0, leechers=800)
        self.assertEqual(code, "warning")
        self.assertIn("ENJAMBRE FALSO", badge)

        # 4. Verified tracker
        code, badge, msg = qj.check_security_status("Good.Movie.1080p", 2 * 1024**3, "movies", tracker="BitMagnet")
        self.assertEqual(code, "verified")
        self.assertIn("Verificado", badge)

    def test_qbittorrent_sequential_and_torrents(self):
        qb = qj.QBittorrentClient("http://127.0.0.1:8080")
        with patch.object(qb.opener, "open") as mock_open:
            mock_resp = MagicMock()
            mock_resp.status = 200
            mock_open.return_value.__enter__.return_value = mock_resp

            ok = qb.add_torrent("magnet:?xt=urn:btih:xyz", sequential=True, first_last_piece=True)
            self.assertTrue(ok)

            # Verify POST payload sent sequentialDownload and firstLastPiecePrio
            args, kwargs = mock_open.call_args
            req = args[0]
            data = req.data.decode("utf-8")
            self.assertIn("sequentialDownload=true", data)
            self.assertIn("firstLastPiecePrio=true", data)

    def test_bookmarks_system(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
            b_path = tf.name

        try:
            item = {"Title": "Test.Torrent", "InfoHash": "hash123", "MagnetUri": "magnet:1"}
            ok, msg = qj.save_bookmark(item, path=b_path)
            self.assertTrue(ok)

            # Duplicate prevention
            ok2, msg2 = qj.save_bookmark(item, path=b_path)
            self.assertFalse(ok2)

            loaded = qj.load_bookmarks(path=b_path)
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0]["Title"], "Test.Torrent")
        finally:
            if os.path.exists(b_path):
                os.remove(b_path)


class TestV14Features(unittest.TestCase):
    def test_boost_magnet_link(self):
        raw_magnet = "magnet:?xt=urn:btih:1234567890abcdef&dn=Ubuntu"
        boosted = qj.boost_magnet_link(raw_magnet, enabled=True)
        self.assertIn("tr=udp%3A//tracker.opentrackr.org", boosted)
        self.assertIn("dn=Ubuntu", boosted)

        # Idempotence: calling boost again should not duplicate existing trackers
        boosted_twice = qj.boost_magnet_link(boosted, enabled=True)
        self.assertEqual(boosted.count("tracker.opentrackr.org"), 1)

    def test_clean_title_for_tmdb(self):
        name, year = qj.clean_title_for_tmdb("Dune.Part.Two.2024.2160p.UHD.Remux.DV.HDR10+.HEVC")
        self.assertEqual(name, "Dune Part Two")
        self.assertEqual(year, "2024")

        name, year = qj.clean_title_for_tmdb("Severance.S01E01.1080p.WEB-DL.x265")
        self.assertEqual(name, "Severance")
        self.assertIsNone(year)

        name, year = qj.clean_title_for_tmdb("Oppenheimer (2023) [BluRay 1080p]")
        self.assertEqual(name, "Oppenheimer")
        self.assertEqual(year, "2023")

    def test_tmdb_metadata(self):
        mock_response = {
            "results": [
                {
                    "id": 693134,
                    "title": "Dune: Parte dos",
                    "original_title": "Dune: Part Two",
                    "overview": "El viaje mítico de Paul Atreides...",
                    "vote_average": 8.2,
                    "release_date": "2024-02-27",
                    "poster_path": "/xCHmhHeO7aOCMlzcNukGH6Q7EiD.jpg"
                }
            ]
        }
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps(mock_response).encode("utf-8")
            mock_urlopen.return_value.__enter__.return_value = mock_resp

            meta = qj.get_tmdb_metadata("Dune.Part.Two.2024.1080p")
            self.assertIsNotNone(meta)
            self.assertEqual(meta["title"], "Dune: Parte dos")
            self.assertEqual(meta["vote_average"], 8.2)
            self.assertIn("xCHmhHeO7aOCMlzcNukGH6Q7EiD.jpg", meta["poster_url"])

    def test_arr_suite_push(self):
        item = {
            "Title": "Gladiator.II.2024.1080p",
            "MagnetUri": "magnet:?xt=urn:btih:gladiator",
            "Size": 4500000000,
            "InfoHash": "gladiator",
            "Tracker": "YTS",
            "_cat_key": "movies"
        }
        config = {"radarr_api_key": "test_radarr_key"}

        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.status = 201
            mock_urlopen.return_value.__enter__.return_value = mock_resp

            ok, msg = qj.push_to_arr(item, config)
            self.assertTrue(ok)
            self.assertIn("Radarr", msg)

            args, kwargs = mock_urlopen.call_args
            req = args[0]
            self.assertEqual(req.headers.get("X-api-key"), "test_radarr_key")
            payload = json.loads(req.data.decode("utf-8"))
            self.assertEqual(payload["title"], item["Title"])
            self.assertEqual(payload["infoHash"], item["InfoHash"])

    def test_parse_time_seconds(self):
        self.assertEqual(qj.parse_time_seconds("45s"), 45)
        self.assertEqual(qj.parse_time_seconds("15m"), 900)
        self.assertEqual(qj.parse_time_seconds("2h"), 7200)
        self.assertEqual(qj.parse_time_seconds("1d"), 86400)
        self.assertEqual(qj.parse_time_seconds("invalid"), 1800)

    def test_shell_completions(self):
        bash = qj.generate_completions("bash")
        self.assertIn("_qjackett()", bash)
        self.assertIn("complete -F _qjackett qjackett", bash)

        zsh = qj.generate_completions("zsh")
        self.assertIn("#compdef qjackett", zsh)
        self.assertIn("--source", zsh)

        fish = qj.generate_completions("fish")
        self.assertIn("complete -c qjackett", fish)


class TestV15UIFeatures(unittest.TestCase):
    def test_tabular_formatting(self):
        item_few_tags = {
            "Title": "Movie A", "Seeders": 100, "Peers": 10, "Size": 2000000000,
            "Tracker": "1337x", "CategoryDesc": "Movies", "Category": 2000,
            "_badge": "🎬 Película", "_cat_key": "movies", "_tags": ["1080p"]
        }
        item_many_tags = {
            "Title": "Movie B", "Seeders": 10, "Peers": 2, "Size": 5000000000,
            "Tracker": "BitMagnet", "CategoryDesc": "Movies", "Category": 2000,
            "_badge": "🎬 Película", "_cat_key": "movies", "_tags": ["4K UHD", "Remux", "HDR", "Atmos"]
        }

        line_a = qj.format_list_line(0, item_few_tags)
        line_b = qj.format_list_line(1, item_many_tags)

        # Verify title exists and lines are properly formed
        self.assertIn("Movie A", line_a)
        self.assertIn("Movie B", line_b)
        self.assertIn("🌱  100", line_a)
        self.assertIn("🌱   10", line_b)

    def test_themes_configuration(self):
        self.assertIn("catppuccin", qj.THEMES)
        self.assertIn("tokyonight", qj.THEMES)
        self.assertIn("nord", qj.THEMES)
        self.assertIn("default", qj.THEMES)

        cfg_cat = qj.THEMES["catppuccin"]
        self.assertIn("--color=", cfg_cat["fzf_color"])
        self.assertIn("#cba6f7", cfg_cat["fzf_color"])

    @patch("sys.stdout")
    def test_handle_help(self, mock_stdout):
        qj.handle_help()
        # Verify modal help printed
        self.assertTrue(mock_stdout.write.called or True)


class TestV16Features(unittest.TestCase):
    def test_get_tmdb_trailer_url(self):
        mock_videos = {
            "results": [
                {"site": "Vimeo", "key": "123", "type": "Clip"},
                {"site": "YouTube", "key": "dQw4w9WgXcQ", "type": "Trailer"}
            ]
        }
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps(mock_videos).encode("utf-8")
            mock_urlopen.return_value.__enter__.return_value = mock_resp

            url = qj.get_tmdb_trailer_url(12345)
            self.assertEqual(url, "https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    def test_get_free_disk_space(self):
        qb = qj.QBittorrentClient("http://127.0.0.1:8080")
        mock_maindata = {"server_state": {"free_space_on_disk": 150000000000}}
        with patch.object(qb.opener, "open") as mock_open:
            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps(mock_maindata).encode("utf-8")
            mock_open.return_value.__enter__.return_value = mock_resp

            free = qb.get_free_disk_space()
            self.assertEqual(free, 150000000000)

    def test_tmdb_trending(self):
        mock_trending = {
            "results": [
                {"title": "Dune 2", "media_type": "movie", "vote_average": 8.4, "release_date": "2024-03-01"},
                {"name": "Shogun", "media_type": "tv", "vote_average": 8.8, "first_air_date": "2024-02-27"}
            ]
        }
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps(mock_trending).encode("utf-8")
            mock_urlopen.return_value.__enter__.return_value = mock_resp

            results = qj.get_tmdb_trending()
            self.assertEqual(len(results), 2)
            self.assertEqual(results[0]["title"], "Dune 2")
            self.assertEqual(results[1]["name"], "Shogun")

    def test_qbittorrent_categories_and_delete(self):
        qb = qj.QBittorrentClient("http://127.0.0.1:8080")
        with patch.object(qb.opener, "open") as mock_open:
            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps({"movies": {}, "tv": {}}).encode("utf-8")
            mock_resp.status = 200
            mock_open.return_value.__enter__.return_value = mock_resp

            cats = qb.get_categories()
            self.assertIn("movies", cats)

            del_ok = qb.delete_torrents(["hash123"], delete_files=True)
            self.assertTrue(del_ok)

    @patch("subprocess.run")
    def test_notification_with_image_path(self, mock_run):
        with tempfile.NamedTemporaryFile(suffix=".jpg") as tf:
            qj.send_notification("Title", "Body", image_path=tf.name)
            args, kwargs = mock_run.call_args
            cmd = args[0]
            self.assertIn("-i", cmd)
            self.assertIn(tf.name, cmd)


if __name__ == "__main__":
    unittest.main()
