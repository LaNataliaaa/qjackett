# Maintainer: LaNataliaaa <33694493+LaNataliaaa@users.noreply.github.com>
pkgname=qjackett-git
pkgver=1.2.0
pkgrel=1
pkgdesc="A lightning-fast interactive TUI torrent searcher powered by Jackett and fzf with direct qBittorrent injection"
arch=('any')
url="https://github.com/LaNataliaaa/qjackett"
license=('MIT')
depends=('python' 'fzf' 'libnotify')
optdepends=(
    'wl-clipboard: clipboard support on Wayland'
    'xclip: clipboard support on X11'
    'xsel: alternative clipboard support on X11'
    'xdg-utils: open torrent tracker links in default browser'
    'jackett: local torrent indexer provider'
    'qbittorrent: torrent download client'
)
provides=('qjackett')
conflicts=('qjackett')
source=("git+https://github.com/LaNataliaaa/qjackett.git")
md5sums=('SKIP')

pkgver() {
    cd "${srcdir}/qjackett"
    printf "1.2.0.r%s.%s" "$(git rev-list --count HEAD)" "$(git rev-parse --short HEAD)"
}

package() {
    cd "${srcdir}/qjackett"
    install -Dm755 qjackett "${pkgdir}/usr/bin/qjackett"
    install -Dm644 LICENSE "${pkgdir}/usr/share/licenses/${pkgname}/LICENSE"
    install -Dm644 README.md "${pkgdir}/usr/share/doc/${pkgname}/README.md"
}
