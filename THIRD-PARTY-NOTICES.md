# Third-party notices

Original application code is MIT. This does not change the licences of dependencies. Julius and Duckling are workflow references, not imported source or assets. No proprietary animation engine, model weights or reference recordings are distributed. System fonts belong to the operating system and are not bundled.

| Component | Pinned version | Licence / source |
| --- | --- | --- |
| DuckDB Python/native engine | 1.4.3 | MIT, https://github.com/duckdb/duckdb/tree/v1.4.3 |
| PySide6 Essentials and Shiboken6 | 6.10.2 | LGPL-3.0-only (our chosen option), https://code.qt.io/pyside/pyside-setup.git/ |
| Qt Core/Gui/Widgets/DBus/Network/Svg and image-format plugins | 6.10.2 | LGPLv3 plus bundled third-party notices, https://code.qt.io/qt/qtbase.git/ |
| openpyxl | 3.1.5 | MIT, https://pypi.org/project/openpyxl/3.1.5/ |
| et-xmlfile | 2.0.0 | MIT and included Python notice, https://pypi.org/project/et-xmlfile/2.0.0/ |
| defusedxml | 0.7.1 | PSF licence, https://pypi.org/project/defusedxml/0.7.1/ |
| Python | build interpreter 3.13.16 | PSF licence and bundled notices, https://www.python.org/downloads/source/ |
| OpenSSL | 3.5.9 in tested interpreter | Apache-2.0, https://github.com/openssl/openssl |
| liblzma (xz) | installed build dependency | bundled COPYING and licence texts, https://tukaani.org/xz/ |
| libmpdec | installed build dependency | BSD-style COPYRIGHT, https://www.bytereef.org/mpdecimal/ |
| PyInstaller bootloader | 6.18.0 | GPL with distribution exception, https://pyinstaller.org/en/stable/license.html |

Full licence texts are in `licenses/`, also bundled under the app Resources/framework directories. Build tooling licence copies are retained; `dependency-inventory.json` in each package records exact installed versions. Only Qt modules detected in the frozen executable are claimed shipped; check the package's framework inventory for actual contents.

Qt is dynamically linked and unmodified. You may inspect, modify and replace the LGPL-covered libraries, including for debugging modifications. Rebuild using the provided source and build recipe with your compatible Qt/PySide version, or replace the dynamic frameworks and bindings in `Contents/Frameworks` and re-sign your local bundle with an ad-hoc signature. No account, secret signing key or developer service is needed to build locally. Source and upstream source links above are provided for LGPL compliance; no restriction on reverse engineering those libraries is imposed by this application. App bundles are not notarised and their local ad-hoc signatures are not publisher identity certificates.
