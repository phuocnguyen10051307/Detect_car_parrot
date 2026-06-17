import unittest

from parser import (
    detect_document_type,
    extract_engine,
    extract_frame,
    extract_issue_date,
    extract_plate,
)


class ParserTests(unittest.TestCase):
    def test_old_document_type_and_extraction(self):
        lines = [
            "Ten chu xe (Owner's full name): CTY VAN TAI ABC",
            "So may (Engine N°): G3LAEP156079",
            "So khung (Chassis N°): KNABE911BFT938030",
            "Hoai Duc, ngay 29 thang 06 nam 2022",
            "Bien so dang ky (N° plate): 29D-310.78",
            "Gia tri den ngay (Date of expiry): 31/12/2039",
            "Dang ky lan dau ngay: 22/05/2017",
        ]

        self.assertEqual(detect_document_type(lines), {"document_type": "old"})
        self.assertEqual(extract_plate(lines), "29D-310.78")
        self.assertEqual(extract_engine(lines), "G3LAEP156079")
        self.assertEqual(extract_frame(lines), "KNABE911BFT938030")
        self.assertEqual(extract_issue_date(lines), "29/06/2022")

    def test_new_document_type_and_extraction(self):
        lines = [
            "GIAY CHUNG NHAN DANG KY XE",
            "So seri: AB123456",
            "Bien so xe: 51H-12345",
            "So may: RL9WCHMUMN123456",
            "So khung: ME4JC1234KT567890",
            "Ngay cap: 15/05/2024",
            "Co hieu luc den: 15/05/2034",
        ]

        self.assertEqual(detect_document_type(lines), {"document_type": "new"})
        self.assertEqual(extract_plate(lines), "51H-12345")
        self.assertEqual(extract_engine(lines), "RL9WCHMUMN123456")
        self.assertEqual(extract_frame(lines), "ME4JC1234KT567890")
        self.assertEqual(extract_issue_date(lines), "15/05/2024")

    def test_unknown_document_type(self):
        lines = [
            "Van ban khong ro loai",
            "Thong tin khong day du",
        ]

        self.assertEqual(detect_document_type(lines), {"document_type": "unknown"})


if __name__ == "__main__":
    unittest.main()
