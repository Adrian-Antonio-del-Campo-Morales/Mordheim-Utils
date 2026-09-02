#!/usr/bin/env python3
"""Combina los YAML de cada directorio de una KB en archivos de texto separados."""

from __future__ import annotations

import argparse
from pathlib import Path


SEPARATOR = "=" * 80


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Genera un .txt por cada subdirectorio de la KB, combinando "
            "recursivamente sus archivos .yaml y .yml."
        )
    )
    parser.add_argument(
        "kb_path",
        nargs="?",
        type=Path,
        default=Path.cwd(),
        help="Directorio padre/raíz de la KB (por defecto: directorio actual).",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("kb-combinada"),
        help="Directorio de salida (por defecto: kb-combinada).",
    )
    return parser.parse_args()


def write_delimiter(output, label: str, file_path: Path, root: Path) -> None:
    """Escribe el bloque de inicio o fin con metadatos del fichero."""
    try:
        relative_path = file_path.relative_to(root)
    except ValueError:
        relative_path = file_path

    output.write(f"{SEPARATOR}\n")
    output.write(f"{label}\n")
    output.write(f"Nombre: {file_path.name}\n")
    output.write(f"Ruta relativa: {relative_path}\n")
    output.write(f"{SEPARATOR}\n")


def yaml_files_in(directory: Path) -> list[Path]:
    """Devuelve los YAML del directorio, incluidas sus subcarpetas."""
    return sorted(
        (
            path for path in directory.rglob("*")
            if path.is_file() and path.suffix.lower() in {".yaml", ".yml"}
        ),
        key=lambda path: str(path).lower(),
    )


def main() -> None:
    args = parse_arguments()
    root = args.kb_path.expanduser().resolve()
    output_directory = args.output.expanduser().resolve()

    if not root.is_dir():
        raise SystemExit(f"Error: la ruta de la KB no es un directorio válido: {root}")

    directories = sorted(
        (path for path in root.iterdir() if path.is_dir() and path.resolve() != output_directory),
        key=lambda path: path.name.lower(),
    )

    output_directory.mkdir(parents=True, exist_ok=True)
    total_files = 0
    for directory in directories:
        yaml_files = yaml_files_in(directory)
        output_path = output_directory / f"{directory.name}.txt"

        with output_path.open("w", encoding="utf-8", newline="\n") as output:
            for file_path in yaml_files:
                write_delimiter(output, "INICIO DE ARCHIVO", file_path, root)
                output.write("\n")

                try:
                    output.write(file_path.read_text(encoding="utf-8"))
                except UnicodeDecodeError:
                    output.write(
                        "[No se pudo leer como UTF-8. "
                        "Convierte este archivo a UTF-8 para incluirlo.]\n"
                    )
                except OSError as error:
                    output.write(f"[No se pudo leer el archivo: {error}]\n")

                if file_path.stat().st_size:
                    output.write("\n")
                write_delimiter(output, "FIN DE ARCHIVO", file_path, root)
                output.write("\n")

        total_files += len(yaml_files)
        print(f"{directory.name}: {len(yaml_files)} archivo(s) -> {output_path}")

    print(
        f"Combinación terminada: {total_files} YAML repartidos en "
        f"{len(directories)} archivo(s) de salida."
    )
    print(f"Directorio de resultados: {output_directory}")


if __name__ == "__main__":
    main()
