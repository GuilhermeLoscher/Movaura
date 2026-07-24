from __future__ import annotations

import importlib.metadata as metadata
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from license_compliance_common import (
    DOCS_AUDIT,
    MOVAURA_BETA,
    PROJECT_ROOT,
    RELEASE_COMPLIANCE,
    ensure_dirs,
    environment_snapshot,
    file_manifest,
    reparse_manifest,
    run_command,
    sha256_file,
    write_csv,
    write_json,
)


RUNTIME_PACKAGES = ["PySide6", "PySide6_Addons", "PySide6_Essentials", "shiboken6", "pywin32", "Pillow"]
BUILD_PACKAGES = ["pyinstaller", "pyinstaller-hooks-contrib", "altgraph", "packaging", "pefile", "pywin32-ctypes"]


def read_json(path: Path, default: object) -> object:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def run_script(name: str) -> dict[str, object]:
    return run_command([sys.executable, str(PROJECT_ROOT / "scripts" / name)], timeout=600)


def collect_license_files(package_name: str) -> list[Path]:
    try:
        dist = metadata.distribution(package_name)
    except metadata.PackageNotFoundError:
        return []
    root = Path(dist.locate_file(""))
    files = []
    for item in dist.files or []:
        path = Path(dist.locate_file(item))
        lower = path.name.lower()
        if path.is_file() and any(token in lower for token in ("license", "copying", "notice", "authors")):
            files.append(path)
    return sorted(set(files), key=lambda path: str(path).lower())


def copy_license_payload() -> list[dict[str, object]]:
    copied: list[dict[str, object]] = []
    for package in [*RUNTIME_PACKAGES, *BUILD_PACKAGES]:
        target = PROJECT_ROOT / "licenses" / package.lower().replace("_", "-")
        target.mkdir(parents=True, exist_ok=True)
        try:
            dist = metadata.distribution(package)
            version = dist.version
            home = dist.metadata.get("Home-page") or dist.metadata.get("Project-URL") or ""
        except metadata.PackageNotFoundError:
            version = "missing"
            home = ""
        (target / "SOURCE.txt").write_text(f"Package: {package}\nVersion: {version}\nSource: {home}\n", encoding="utf-8")
        for source in collect_license_files(package):
            destination = target / source.name
            shutil.copyfile(source, destination)
            copied.append(
                {
                    "package": package,
                    "version": version,
                    "source": str(source),
                    "destination": str(destination.relative_to(PROJECT_ROOT)),
                    "sha256": sha256_file(destination),
                }
            )
    write_json(RELEASE_COMPLIANCE / "licenses" / "copied-package-license-files.json", copied)
    return copied


def copy_ffmpeg_source_skeleton() -> None:
    root = PROJECT_ROOT / "third_party_sources" / "ffmpeg"
    (root / "PATCHES").mkdir(parents=True, exist_ok=True)
    (root / "LICENSES").mkdir(parents=True, exist_ok=True)
    config = PROJECT_ROOT / "licenses" / "ffmpeg" / "BUILD_CONFIGURATION.txt"
    (root / "README.txt").write_text(
        "Corresponding FFmpeg source package is not complete yet.\n"
        "Before commercial distribution, replace these placeholders with an immutable source archive, checksum, build provenance and patches.\n",
        encoding="utf-8",
    )
    (root / "SOURCE_URL.txt").write_text("PENDING - immutable corresponding source URL required.\n", encoding="utf-8")
    (root / "SOURCE_SHA256.txt").write_text("PENDING - source archive SHA-256 required.\n", encoding="utf-8")
    (root / "BUILD_CONFIGURATION.txt").write_text(config.read_text(encoding="utf-8") if config.exists() else "PENDING\n", encoding="utf-8")
    write_json(
        root / "BUILD_PROVENANCE.json",
        {
            "status": "PENDING",
            "reason": "Current FFmpeg binary is not locked to an immutable source/archive provenance.",
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
        },
    )
    (root / "CHECKSUMS.txt").write_text("PENDING - generated after immutable source archive is selected.\n", encoding="utf-8")


def markdown_table(rows: list[dict[str, object]], columns: list[str]) -> str:
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = []
    for row in rows:
        body.append("| " + " | ".join(str(row.get(column, "")).replace("\n", " ") for column in columns) + " |")
    return "\n".join([header, separator, *body])


def qt_docs() -> None:
    matrix = read_json(RELEASE_COMPLIANCE / "qt" / "qt-module-license-matrix.json", [])
    columns = [
        "file_module",
        "version",
        "origin",
        "official_license",
        "lgpl_available",
        "gpl_only",
        "used",
        "evidence",
        "decision",
    ]
    text = "# Qt/PySide6 module license matrix\n\n"
    text += "Status: REVIEW REQUIRED. This matrix is generated from the local PySide6/Qt payload and must be checked against official Qt module licensing before release.\n\n"
    text += markdown_table(matrix if isinstance(matrix, list) else [], columns) + "\n"
    (PROJECT_ROOT / "docs" / "QT_MODULE_LICENSE_MATRIX.md").write_text(text, encoding="utf-8")


def python_docs() -> None:
    rows = read_json(RELEASE_COMPLIANCE / "python" / "python-dependency-license-matrix.json", [])
    columns = ["name", "version", "source", "license", "runtime", "build_only", "official_license_file", "risk"]
    text = "# Python dependency license matrix\n\n"
    text += "Status: REVIEW REQUIRED. License values come from installed distribution metadata and copied package license files.\n\n"
    text += markdown_table(rows if isinstance(rows, list) else [], columns) + "\n"
    (PROJECT_ROOT / "docs" / "PYTHON_DEPENDENCY_LICENSE_MATRIX.md").write_text(text, encoding="utf-8")


def ffmpeg_docs() -> None:
    audit = read_json(RELEASE_COMPLIANCE / "ffmpeg" / "ffmpeg-audit.json", {})
    libs = audit.get("external_libraries", []) if isinstance(audit, dict) else []
    rows = []
    for flag in libs:
        rows.append(
            {
                "library": flag,
                "official_license": "PENDING OFFICIAL VERIFICATION",
                "version": "PENDING",
                "source": "PENDING",
                "effect_on_ffmpeg": "REVIEW REQUIRED",
                "patent_risk": "REVIEW REQUIRED",
                "status": "BLOCKER UNTIL CLASSIFIED",
            }
        )
    text = "# FFmpeg external library matrix\n\n"
    text += "Status: NOT READY - LICENSE BLOCKERS. Each external library enabled in FFmpeg needs source, license and patent review.\n\n"
    text += markdown_table(rows, ["library", "official_license", "version", "source", "effect_on_ffmpeg", "patent_risk", "status"]) + "\n"
    (PROJECT_ROOT / "docs" / "FFMPEG_EXTERNAL_LIBRARY_MATRIX.md").write_text(text, encoding="utf-8")

    lock = read_json(PROJECT_ROOT / "third_party" / "ffmpeg" / "LOCK.json", {})
    (PROJECT_ROOT / "docs" / "FFMPEG_BUILD_LOCK.md").write_text(
        "# FFmpeg build lock\n\n"
        "Status: NOT READY - LICENSE BLOCKERS.\n\n"
        "The current package still needs an immutable FFmpeg artifact/source lock before commercial release.\n\n"
        f"- Version: {lock.get('ffmpeg_version', 'unknown') if isinstance(lock, dict) else 'unknown'}\n"
        f"- Commit: {lock.get('ffmpeg_commit', 'unknown') if isinstance(lock, dict) else 'unknown'}\n"
        f"- Archive SHA-256: {lock.get('archive_sha256', 'PENDING') if isinstance(lock, dict) else 'PENDING'}\n"
        f"- Audit status: {lock.get('audit_status', 'PENDING') if isinstance(lock, dict) else 'PENDING'}\n\n"
        "See `third_party/ffmpeg/LOCK.json` and `release/compliance/ffmpeg/ffmpeg-audit.json`.\n",
        encoding="utf-8",
    )


def core_docs() -> None:
    head = run_command(["git", "rev-parse", "HEAD"]).get("stdout", "").strip()
    created = datetime.now(timezone.utc).isoformat()
    (PROJECT_ROOT / "docs" / "LGPL_MSIX_TECHNICAL_ASSESSMENT.md").write_text(
        "# LGPL and MSIX technical assessment\n\n"
        "Status: OWNER DECISION REQUIRED.\n\n"
        "This is a technical assessment, not legal advice. MSIX packages are installed into protected app package locations and are signature-bound. "
        "That can complicate the user's ability to replace LGPL libraries with modified versions without rebuilding/repackaging the application.\n\n"
        "Options for owner/legal review:\n\n"
        "1. Qt Community/LGPLv3: keep DLLs separate, provide notices/source/rebuild materials, and have counsel confirm the MSIX replacement/relink strategy.\n"
        "2. Qt commercial license: obtain and keep proof of license coverage for distributed Qt modules.\n"
        "3. Framework replacement: analyze only if Qt obligations cannot be satisfied.\n\n"
        "Security constraints: do not load DLLs from the current directory, global PATH, user-writable untrusted folders, or unsigned paths.\n",
        encoding="utf-8",
    )
    (PROJECT_ROOT / "docs" / "CODEC_PATENT_RISK_REGISTER.md").write_text(
        "# Codec patent risk register\n\n"
        "Status: LEGAL REVIEW REQUIRED.\n\n"
        "| Codec/Feature | Use in Movaura | Provider | Territory | Risk | Action |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
        "| H.264/AVC | Playback/import/optimization depending on user media and FFmpeg build | Windows/FFmpeg | PENDING | Patent/licensing review required | Counsel to confirm commercial distribution rules. |\n"
        "| H.265/HEVC | Playback if supported by system/user files | Windows/FFmpeg | PENDING | Patent/licensing review required | Confirm Store/device codec availability and terms. |\n"
        "| VP8/VP9/AV1 | Playback/import if provided by files/codecs | Windows/FFmpeg | PENDING | Review required | Confirm codec/library notices and patent position. |\n"
        "| GIF/WebP/PNG/JPEG | Wallpaper import/playback/static assets | App libraries/Windows | PENDING | Review required | Confirm third-party library notices. |\n",
        encoding="utf-8",
    )
    (PROJECT_ROOT / "docs" / "EULA_DRAFT_PT_BR.md").write_text(
        "# MODELO PARA REVISAO JURIDICA - NAO PUBLICAR SEM APROVACAO PROFISSIONAL\n\n"
        "Este rascunho e tecnico e deve ser revisado por advogado antes de uso.\n\n"
        "## Licenca de uso\n"
        "O proprietario concede ao usuario uma licenca limitada para instalar e usar o Movaura conforme os termos comerciais a definir.\n\n"
        "## Componentes de terceiros\n"
        "O Movaura inclui componentes de terceiros. As licencas desses componentes prevalecem quando concedem direitos que este EULA nao pode restringir.\n\n"
        "## Engenharia reversa\n"
        "Qualquer restricao de engenharia reversa deve preservar direitos legais e direitos necessarios para exercer licencas de terceiros, incluindo LGPL/GPL quando aplicavel.\n\n"
        "## Campos pendentes\n"
        "CNPJ/endereco, jurisdicao, preco, reembolso, suporte, cancelamento, garantia, paises de venda e contato oficial.\n",
        encoding="utf-8",
    )
    (PROJECT_ROOT / "docs" / "EULA_DRAFT_EN_US.md").write_text(
        "# TEMPLATE FOR LEGAL REVIEW - DO NOT PUBLISH WITHOUT PROFESSIONAL APPROVAL\n\n"
        "This draft is technical and must be reviewed by counsel before use.\n\n"
        "## License grant\n"
        "The owner grants the user a limited license to install and use Movaura under commercial terms to be completed.\n\n"
        "## Third-party components\n"
        "Movaura includes third-party components. Their licenses prevail where they grant rights this EULA cannot restrict.\n\n"
        "## Reverse engineering\n"
        "Any reverse-engineering restriction must preserve legal rights and rights needed to exercise third-party licenses, including LGPL/GPL where applicable.\n\n"
        "## Pending business fields\n"
        "Legal entity, address, jurisdiction, pricing, refunds, support, cancellation, warranty, countries of sale and official contact.\n",
        encoding="utf-8",
    )
    (PROJECT_ROOT / "docs" / "PRIVACY_POLICY.md").write_text(
        "# Politica de privacidade - Movaura\n\n"
        "Status: minuta tecnica para revisao juridica.\n\n"
        "O Movaura processa wallpapers, configuracoes, biblioteca local, logs tecnicos e arquivos importados no computador do usuario.\n\n"
        "## Ativacao/licenciamento\n"
        "Builds que ativam licenciamento podem enviar chave, e-mail informado, nome informado e identificador tecnico de maquina ao servidor de ativacao configurado pelo proprietario. Builds sem licenciamento obrigatorio nao exigem esse envio.\n\n"
        "## IA\n"
        "A versao atual usa provider mock/local. Nenhuma API real de IA foi integrada nesta tarefa.\n\n"
        "## Telemetria\n"
        "Nao foi adicionada telemetria nesta tarefa. Qualquer telemetria futura deve ser opcional, documentada e revisada.\n\n"
        "## Logs\n"
        "Logs tecnicos ficam localmente para diagnostico e podem conter caminhos de arquivos locais. O usuario escolhe quando exportar relatorio de suporte.\n\n"
        "## Revisao\n"
        "Esta politica nao declara conformidade LGPD/GDPR automaticamente. Revisao juridica profissional e necessaria antes de publicacao comercial.\n",
        encoding="utf-8",
    )
    (PROJECT_ROOT / "docs" / "LEGAL_REVIEW_HANDOFF.md").write_text(
        "# Legal review handoff\n\n"
        f"- Product: Movaura\n- Commit: {head}\n- Created UTC: {created}\n- Distribution: Windows standalone/MSIX, Microsoft Store candidate\n- Countries: PENDING OWNER INPUT\n- Business model: PENDING OWNER INPUT\n\n"
        "## Questions for counsel\n\n"
        "1. Does the proposed strategy satisfy LGPLv3 in an MSIX distribution?\n"
        "2. Are LGPL component materials sufficient?\n"
        "3. Does the EULA preserve third-party rights?\n"
        "4. Do codecs require patent licenses in the selected territories?\n"
        "5. Is the FFmpeg source offer sufficient?\n"
        "6. Is any Qt module GPL-only or commercial-only in the artifact?\n"
        "7. Do sales/activation create additional obligations?\n"
        "8. Is the privacy policy adequate?\n\n"
        "## Evidence\n\n"
        "- `release/compliance/`\n- `docs/QT_MODULE_LICENSE_MATRIX.md`\n- `docs/FFMPEG_EXTERNAL_LIBRARY_MATRIX.md`\n- `third_party/ffmpeg/LOCK.json`\n- `THIRD_PARTY_NOTICES.txt`\n",
        encoding="utf-8",
    )


def notices_docs() -> None:
    rows = read_json(RELEASE_COMPLIANCE / "python" / "python-dependency-license-matrix.json", [])
    qt_rows = read_json(RELEASE_COMPLIANCE / "qt" / "qt-module-license-matrix.json", [])
    text = "# Third-party notices\n\n"
    text += "Status: REVIEW REQUIRED. This notice summarizes technical inventory and must be reviewed against official license texts.\n\n"
    text += "## Runtime components\n\n"
    for item in rows if isinstance(rows, list) else []:
        runtime = item.get("runtime")
        if runtime:
            text += f"- {item.get('name')} {item.get('version')} - {item.get('license')} - license files: {item.get('official_license_file')}\n"
    text += "\n## Qt/PySide6 payload\n\n"
    text += f"- Qt/PySide/Shiboken files inventoried: {len(qt_rows) if isinstance(qt_rows, list) else 0}\n"
    text += "- See `docs/QT_MODULE_LICENSE_MATRIX.md` for per-file review status.\n\n"
    text += "## FFmpeg\n\n"
    text += "- FFmpeg is bundled for optional local video optimization.\n"
    text += "- Current status: NOT READY until immutable artifact/source lock and external library review are completed.\n"
    text += "- See `docs/FFMPEG_BUILD_LOCK.md` and `third_party/ffmpeg/LOCK.json`.\n"
    (PROJECT_ROOT / "docs" / "THIRD_PARTY_NOTICES.md").write_text(text, encoding="utf-8")
    (PROJECT_ROOT / "THIRD_PARTY_NOTICES.txt").write_text(text.replace("# ", "").replace("## ", ""), encoding="utf-8")

    component_rows = []
    for item in rows if isinstance(rows, list) else []:
        component_rows.append(
            {
                "component": item.get("name"),
                "version": item.get("version"),
                "license": item.get("license"),
                "redistributed": item.get("runtime"),
                "status": item.get("risk"),
            }
        )
    component_rows.append(
        {
            "component": "FFmpeg",
            "version": "see third_party/ffmpeg/LOCK.json",
            "license": "PENDING FINAL CLASSIFICATION",
            "redistributed": "yes",
            "status": "BLOCKED",
        }
    )
    (PROJECT_ROOT / "docs" / "THIRD_PARTY_COMPONENTS_LOCK.md").write_text(
        "# Third-party components lock\n\n"
        + markdown_table(component_rows, ["component", "version", "license", "redistributed", "status"])
        + "\n",
        encoding="utf-8",
    )


def final_docs(command_results: dict[str, object]) -> None:
    blockers = [
        "FFmpeg immutable archive/source lock is pending.",
        "FFmpeg external libraries require official per-library review.",
        "Qt module licensing still requires official module-by-module confirmation.",
        "LGPLv3 and MSIX replacement/relink strategy requires owner/legal decision.",
        "Patent/codecs review requires territory-specific legal review.",
    ]
    report = "# License compliance test report\n\n"
    for name, result in command_results.items():
        report += f"## {name}\n\n```json\n{json.dumps(result, indent=2, ensure_ascii=False)[:5000]}\n```\n\n"
    (PROJECT_ROOT / "docs" / "LICENSE_COMPLIANCE_TEST_REPORT.md").write_text(report, encoding="utf-8")
    (PROJECT_ROOT / "docs" / "FINAL_LICENSE_AUDIT.md").write_text(
        "# Final license audit\n\n"
        "Status: NOT READY - LICENSE BLOCKERS\n\n"
        "This is a technical compliance preparation report, not legal advice.\n\n"
        "## Blockers\n\n"
        + "\n".join(f"- {item}" for item in blockers)
        + "\n\n## Evidence\n\n"
        "- `release/compliance/`\n- `docs/audit-evidence/movaura-beta-baseline.json`\n- `third_party/ffmpeg/LOCK.json`\n- `THIRD_PARTY_NOTICES.txt`\n",
        encoding="utf-8",
    )


def sbom() -> None:
    rows = read_json(RELEASE_COMPLIANCE / "python" / "python-dependency-license-matrix.json", [])
    packages = []
    for item in rows if isinstance(rows, list) else []:
        packages.append(
            {
                "SPDXID": f"SPDXRef-Package-{item.get('name', 'unknown')}",
                "name": item.get("name"),
                "versionInfo": item.get("version"),
                "licenseConcluded": item.get("license") or "NOASSERTION",
                "licenseDeclared": item.get("license") or "NOASSERTION",
                "downloadLocation": item.get("source") or "NOASSERTION",
            }
        )
    payload = {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": "Movaura technical SBOM",
        "documentNamespace": f"https://movaura.local/spdx/{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        "creationInfo": {
            "created": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "creators": ["Tool: Movaura license compliance scripts"],
        },
        "packages": packages,
    }
    write_json(RELEASE_COMPLIANCE / "inventories" / "sbom-spdx.json", payload)


def main() -> int:
    ensure_dirs()
    command_results = {
        "environment": environment_snapshot(),
        "audit_qt_modules": run_script("audit_qt_modules.py"),
        "audit_python_licenses": run_script("audit_python_licenses.py"),
        "audit_ffmpeg_compliance": run_script("audit_ffmpeg_compliance.py"),
    }
    write_json(RELEASE_COMPLIANCE / "environment" / "baseline.json", command_results["environment"])
    write_json(DOCS_AUDIT / "movaura-beta-baseline.json", file_manifest(MOVAURA_BETA, hash_limit_bytes=100 * 1024 * 1024))
    write_json(DOCS_AUDIT / "movaura-beta-links.json", reparse_manifest(MOVAURA_BETA))
    write_json(RELEASE_COMPLIANCE / "inventories" / "project-file-manifest.json", file_manifest(PROJECT_ROOT, hash_limit_bytes=25 * 1024 * 1024))
    write_json(RELEASE_COMPLIANCE / "inventories" / "project-reparse-points.json", reparse_manifest(PROJECT_ROOT))
    write_json(RELEASE_COMPLIANCE / "inventories" / "standalone-file-manifest.json", file_manifest(PROJECT_ROOT / "dist" / "standalone" / "Movaura", hash_limit_bytes=100 * 1024 * 1024))
    write_json(RELEASE_COMPLIANCE / "msix" / "msix-file-manifest.json", file_manifest(PROJECT_ROOT / "release" / "msix", hash_limit_bytes=100 * 1024 * 1024))
    write_json(RELEASE_COMPLIANCE / "environment" / "pip-freeze.json", run_command([sys.executable, "-m", "pip", "freeze"]))
    write_json(RELEASE_COMPLIANCE / "environment" / "pip-inspect.json", run_command([sys.executable, "-m", "pip", "inspect"], timeout=300))
    copy_license_payload()
    copy_ffmpeg_source_skeleton()
    qt_docs()
    python_docs()
    ffmpeg_docs()
    core_docs()
    notices_docs()
    sbom()
    final_docs(command_results)
    write_json(RELEASE_COMPLIANCE / "reports" / "license-compliance-prep-results.json", command_results)
    print("license_compliance_docs=generated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
