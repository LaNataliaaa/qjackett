# Maintainer: LaNataliaaa <33694493+LaNataliaaa@users.noreply.github.com>
pkgname=qjackett-git
pkgver=1.0.0
pkgrel=1
pkgdesc="A lightning-fast interactive TUI torrent searcher powered by Jackett and fzf with direct qBittorrent injection"
arch=('any')
url="https://github.com/LaNataliaaa/qjackett"
license=('MIT')
depends=('python' 'fzf' 'libnotify' 'wl-clipboard')
optdepends=(
    'jackett: local torrent indexer provider'
    'qbittorrent: torrent download client'
)
provides=('qjackett')
conflicts=('qjackett')
source=("git+https://github.com/LaNataliaaa/qjackett.git")
md5sums=('SKIP')

package() {
    cd "${srcdir}/qjackett"
    install -Dm755 qjackett "${pkgdir}/usr/bin/qjackett"
    install -Dm644 LICENSE "${pkgdir}/usr/share/licenses/${pkgname}/LICENSE"
}
