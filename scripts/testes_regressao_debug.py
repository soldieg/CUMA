#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Testes de regressão dos defeitos encontrados na auditoria 1.100.36."""
from __future__ import annotations

import hashlib
import os
import shutil
import sys
import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEST_DATA = Path(tempfile.mkdtemp(prefix="cuma_regressao_"))
os.environ["CUMA_USER_DATA_DIR"] = str(TEST_DATA / "user_data")
sys.path.insert(0, str(ROOT))

import fitz  # noqa: E402
import cuma  # noqa: E402
import cuma_updater  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class CumaRegressionTests(unittest.TestCase):
    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(TEST_DATA, ignore_errors=True)

    def setUp(self) -> None:
        self.work = Path(tempfile.mkdtemp(dir=TEST_DATA, prefix="case_"))

    def tearDown(self) -> None:
        shutil.rmtree(self.work, ignore_errors=True)

    def test_import_uses_only_user_data_directory(self) -> None:
        self.assertEqual(cuma.cuma_settings_path().parent, TEST_DATA / "user_data")
        self.assertFalse((ROOT / ".cuma_user_data").exists())
        self.assertFalse((ROOT / "CUMA.log").exists())

    def test_default_double_page_option_does_not_rasterize_portrait_pdf(self) -> None:
        pdf = self.work / "portrait.pdf"
        doc = fitz.open()
        page = doc.new_page(width=595, height=842)
        page.insert_text((72, 100), "TEXTO PESQUISAVEL CUMA")
        doc.save(pdf)
        doc.close()

        before_hash = sha256(pdf)
        before = fitz.open(pdf)
        before_text = before[0].get_text()
        before.close()

        stats = cuma._cuma_11003_process_clean_pdf_in_place(
            pdf,
            settings={
                "split_double_pages": True,
                "auto_crop": False,
                "remove_page_numbers": False,
                "webtoon_split": False,
                "image_preset": "Original",
            },
        )

        after = fitz.open(pdf)
        after_text = after[0].get_text()
        after.close()
        self.assertEqual(stats["transformed_pages"], 0)
        self.assertEqual(before_hash, sha256(pdf))
        self.assertEqual(before_text, after_text)
        self.assertIn("TEXTO PESQUISAVEL", after_text)

    def test_real_landscape_page_is_split(self) -> None:
        pdf = self.work / "landscape.pdf"
        doc = fitz.open()
        page = doc.new_page(width=1200, height=700)
        page.insert_text((72, 100), "PAGINA DUPLA")
        doc.save(pdf)
        doc.close()

        stats = cuma._cuma_11003_process_clean_pdf_in_place(
            pdf,
            settings={
                "split_double_pages": True,
                "reading_order": "Ocidental",
                "auto_crop": False,
                "remove_page_numbers": False,
                "webtoon_split": False,
                "image_preset": "Original",
            },
        )
        result = fitz.open(pdf)
        count = len(result)
        result.close()
        self.assertEqual(stats["transformed_pages"], 1)
        self.assertEqual(stats["double_pages_split"], 1)
        self.assertEqual(count, 2)

    def test_pdf_metadata_preserves_existing_bookmarks_and_keywords(self) -> None:
        pdf = self.work / "bookmarks.pdf"
        doc = fitz.open()
        for _ in range(5):
            doc.new_page()
        original_toc = [
            [1, "Volume 1", 1],
            [2, "Capítulo 1", 1],
            [2, "Capítulo 2", 3],
            [1, "Apêndice", 5],
        ]
        doc.set_toc(original_toc)
        doc.set_metadata({"title": "Original", "keywords": "original; conservar"})
        doc.save(pdf)
        doc.close()

        meta = cuma._cuma_11013_default_metadata(pdf, 5)
        meta["title"] = "Atualizado"
        meta["volumes"] = [{"volume": 1, "title": "Volume 1", "start_page": 1, "end_page": 5}]
        self.assertTrue(cuma._cuma_11013_write_pdf_metadata(pdf, meta))

        check = fitz.open(pdf)
        self.assertEqual(check.get_toc(simple=True), original_toc)
        keywords = check.metadata.get("keywords", "")
        attachments = list(check.embfile_names() or [])
        check.close()
        self.assertIn("original", keywords)
        self.assertIn(cuma.CUMA_11013_METADATA_JSON_NAME, attachments)

    def test_result_size_is_refreshed_after_metadata_step(self) -> None:
        output = self.work / "result.pdf"
        output.write_bytes(b"initial")
        old_clean = cuma._CUMA_11013_OLD_PDF_CLEAN
        old_embed = cuma._cuma_11013_embed_metadata_from_source
        try:
            cuma._CUMA_11013_OLD_PDF_CLEAN = lambda *a, **k: cuma.Result(
                source=str(output),
                output=str(output),
                original_size=100,
                final_size=1,
            )
            def fake_embed(source, target):
                target.write_bytes(target.read_bytes() + b"-metadata")
                return True
            cuma._cuma_11013_embed_metadata_from_source = fake_embed
            result = cuma._cuma_11013_pdf_clean(object(), output, output)
        finally:
            cuma._CUMA_11013_OLD_PDF_CLEAN = old_clean
            cuma._cuma_11013_embed_metadata_from_source = old_embed
        self.assertEqual(result.final_size, output.stat().st_size)
        self.assertEqual(result.saved_bytes, 100 - output.stat().st_size)

    def test_zip_rewrite_preserves_duplicate_entries_by_identity(self) -> None:
        archive = self.work / "duplicate.zip"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(archive, "w") as zf:
                zf.writestr("dup.txt", b"first")
                zf.writestr("dup.txt", b"second")
        self.assertTrue(cuma._cuma_11013_zip_rewrite_with_entries(archive, {"meta.json": b"{}"}))
        with zipfile.ZipFile(archive, "r") as zf:
            duplicates = [item for item in zf.infolist() if item.filename == "dup.txt"]
            values = [zf.read(item) for item in duplicates]
            self.assertEqual(values, [b"first", b"second"])
            self.assertEqual(zf.testzip(), None)


    def test_exact_reported_page_410_moves_to_419(self) -> None:
        metadata = {
            "title": "Exemplo 410 para 419",
            "mode": "multi_volume",
            "total_pages": 500,
            "cover_page": 1,
            "volumes": [
                {"volume": 1, "title": "Volume anterior", "start_page": 1, "end_page": 409, "cover_page": 1},
                {"volume": 2, "title": "Volume 3", "start_page": 410, "end_page": 500, "cover_page": 410},
            ],
        }
        split_pages = {10, 20, 30, 40, 50, 60, 70, 80, 90}
        spans = {}
        output_page = 1
        for source_page in range(1, 501):
            produced = 2 if source_page in split_pages else 1
            spans[source_page] = (output_page, output_page + produced - 1)
            output_page += produced

        remapped = cuma._cuma_11036_remap_metadata(
            metadata,
            spans,
            output_total=509,
            source_total=500,
        )
        self.assertEqual(remapped["volumes"][1]["start_page"], 419)
        self.assertEqual(remapped["volumes"][1]["cover_page"], 419)
        self.assertEqual(remapped["volumes"][0]["end_page"], 418)

    def test_volume_covers_are_remapped_after_double_page_splits(self) -> None:
        source = self.work / "volumes_source.pdf"
        output = self.work / "volumes_output.pdf"

        doc = fitz.open()
        for page_no in range(1, 13):
            if page_no in (2, 7):
                page = doc.new_page(width=1200, height=700)
            else:
                page = doc.new_page(width=600, height=800)
            # A capa do Volume 2 fica vazia de propósito: o metadado deve
            # protegê-la contra a remoção por baixa densidade.
            if page_no != 5:
                page.draw_rect(page.rect, color=(0, 0, 0), fill=(0, 0, 0))
        doc.save(source)
        doc.close()

        metadata = cuma._cuma_11013_default_metadata(source, 12)
        metadata["mode"] = "multi_volume"
        metadata["volumes"] = [
            {"volume": 1, "title": "Volume 1", "start_page": 1, "end_page": 4, "cover_page": 1},
            {"volume": 2, "title": "Volume 2", "start_page": 5, "end_page": 9, "cover_page": 5},
            {"volume": 3, "title": "Volume 3", "start_page": 10, "end_page": 12, "cover_page": 10},
        ]
        self.assertTrue(cuma._cuma_11013_write_pdf_metadata(source, metadata))

        old_settings = cuma._cuma_11000_processing_settings
        cuma._cuma_11000_processing_settings = lambda: {
            "split_double_pages": True,
            "split_keep_original": False,
            "reading_order": "Ocidental",
            "auto_crop": False,
            "remove_page_numbers": False,
            "webtoon_split": False,
            "image_preset": "Original",
        }
        try:
            cfg = cuma.CleanerConfig(
                profile="Conservador",
                mode="visual",
                ranges="",
                keep_first=True,
                keep_last=0,
                export_format="PDF",
                output_dir=str(self.work),
                save_removed_pdf=False,
                validate_output=True,
            )
            result = cuma.PDFCleaner(cfg).clean(source, output)
        finally:
            cuma._cuma_11000_processing_settings = old_settings

        self.assertEqual(result.final_pages, 14)
        remapped = cuma._cuma_11013_read_embedded_metadata(output)
        self.assertIsInstance(remapped, dict)
        self.assertEqual(
            [
                (vol["start_page"], vol["end_page"], vol["cover_page"])
                for vol in remapped["volumes"]
            ],
            [(1, 5, 1), (6, 11, 6), (12, 14, 12)],
        )

        check = fitz.open(output)
        try:
            self.assertEqual(
                check.get_toc(simple=True),
                [[1, "Volume 1", 1], [1, "Volume 2", 6], [1, "Volume 3", 12]],
            )
        finally:
            check.close()

    def test_updater_rejects_path_traversal(self) -> None:
        archive = self.work / "evil.zip"
        with zipfile.ZipFile(archive, "w") as zf:
            zf.writestr("../outside.txt", b"blocked")
        with self.assertRaises(RuntimeError):
            cuma_updater._extract_archive(archive, self.work / "extract", None, "zip")
        self.assertFalse((self.work / "outside.txt").exists())

    def test_updater_rejects_declared_archive_bomb(self) -> None:
        archive = self.work / "large.zip"
        with zipfile.ZipFile(archive, "w") as zf:
            zf.writestr("large.bin", b"1234567890")
        old_limit = cuma_updater.MAX_ARCHIVE_UNCOMPRESSED_BYTES
        try:
            cuma_updater.MAX_ARCHIVE_UNCOMPRESSED_BYTES = 5
            with self.assertRaises(RuntimeError):
                cuma_updater._extract_archive(archive, self.work / "extract", None, "zip")
        finally:
            cuma_updater.MAX_ARCHIVE_UNCOMPRESSED_BYTES = old_limit


if __name__ == "__main__":
    unittest.main(verbosity=2)
