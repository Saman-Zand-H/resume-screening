from itertools import groupby
from typing import NamedTuple

from .scores import CombinedScore


class Assessment(NamedTuple):
    value: str
    label: str


class Assessments(NamedTuple):
    CAST = Assessment("CAST", "Criteria Attention Skills Test")
    CBST = Assessment("CBST", "Criteria Basic Skills Test")
    CCAT = Assessment("CCAT", "Criteria Cognitive Aptitude Test")
    CLIK = Assessment("CLIK", "Computer Literacy and Internet Knowledge Test")
    CLPT_EN = Assessment("CLPT-EN", "Criteria Language Proficiency Test")
    CLPTE_EN = Assessment("CLPTE-EN", "Criteria Language Proficiency Test - Express")
    CMRA = Assessment("CMRA", "Criteria Mechanical Reasoning Assessment")
    COGNIFY = Assessment("Cognify", "Cognify")
    CPI = Assessment("CPI", "Criteria Personality Inventory")
    CSAP = Assessment("CSAP", "Criteria Service Aptitude Profile")
    EPP = Assessment("EPP", "Employee Personality Profile")
    Emotify = Assessment("Emotify", "Emotify")
    Excel16 = Assessment("Excel16", "Excel 2016")
    Excel365 = Assessment("Excel365", "Excel 365 (and Excel 365 Interactive)")
    GAME = Assessment("GAME", "General Aptitude Mobile Evaluation")
    Illustrat = Assessment("Illustrat", "Illustrat")
    MRAB = Assessment("MRAB", "MiniCog Rapid Assessment")
    PPT16 = Assessment("PPT16", "Power Point 2016")
    PPT365 = Assessment("PPT365", "Power Point 365")
    SalesAP = Assessment("SalesAP", "Sales Achievement Predictor")
    TT = Assessment("TT", "Typing Test")
    TenKey = Assessment("TenKey", "Ten Key Test")
    UCAT = Assessment("UCAT", "Universal Cognitive Aptitude Test")
    UCOGNIFY = Assessment("UCognify", "UCognify")
    Word16 = Assessment("Word16", "Word 2016")
    Word365 = Assessment("Word365", "Word 365")
    WPP = Assessment("WPP", "Workplace Productivity Profile")
    WSP_L = Assessment("WSP-L", "Work Safety Profile - Long")
    WSP_S = Assessment("WSP-S", "Work Safety Profile")
    WAA = Assessment("WAA", "Workplace Alignment Assessment")
    WTMA = Assessment("WTMA", "Wiesen Test of Mechanical Aptitude")
    TMXX = Assessment("TMXX", "Test Maker Custom Tests")

    @classmethod
    def get_from_score_name(cls, score_name):
        return next(
            filter(lambda i: isinstance(i, Assessment) and score_name.startswith(i.value), cls.__dict__.values()),
            None,
        )

    @classmethod
    def get_from_scores(cls, scores: CombinedScore):
        scores_dict = scores.model_dump()

        return groupby(scores_dict.items(), lambda k, v: cls.get_from_score_name(k))
