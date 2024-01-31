from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, HttpUrl, RootModel

from .orders import Candidate

GetScoreRequest = RootModel[str]


class RankingScore(BaseModel):
    RankingScore: Optional[int] = None


class CASTScore(BaseModel):
    CASTPercentile: Optional[int] = None
    CASTDividedAttention: Optional[int] = None
    CASTVigilance: Optional[int] = None
    CASTFiltering: Optional[int] = None
    CASTPerceptualReaction: Optional[int] = None


class CBSTScore(BaseModel):
    CBSTRawScore: Optional[int] = None
    CBSTPercentile: Optional[int] = None
    CBSTMathScore: Optional[int] = None
    CBSTVerbalScore: Optional[int] = None


class CCATScore(BaseModel):
    CCATRawScore: Optional[int] = None
    CCATPercentile: Optional[int] = None
    CCATInvalidScore: Optional[int] = None
    CCATSpatialPercentile: Optional[int] = None
    CCATVerbalPercentile: Optional[int] = None
    CCATMathPercentile: Optional[int] = None


class CLIKScore(BaseModel):
    CLIKRawScore: Optional[int] = None
    CLICKRanking: Optional[Literal["Not Proficient", "Proficient", "Highly Proficient"]] = None


class CLPTEnglishScore(BaseModel):
    CLPTEnglishOverallScore: Optional[int] = None
    CLPTEnglishOverallProficiency: Optional[str] = None
    CLPTEnglishReadingScore: Optional[int] = None
    CLPTEnglishReadingProficiency: Optional[str] = None
    CLPTEnglishReadingCEFR: Optional[Literal["A1", "A2", "B1", "B2", "C1", "C2"]] = None
    CLPTEnglishListeningScore: Optional[int] = None
    CLPTEnglishListeningProficiency: Optional[str] = None
    CLPTEnglishListeningCEFR: Optional[Literal["A1", "A2", "B1", "B2", "C1", "C2"]] = None
    CLPTEnglishWritingScore: Optional[int] = None
    CLPTEnglishWritingProficiency: Optional[str] = None
    CLPTEnglishWritingCEFR: Optional[Literal["A1", "A2", "B1", "B2", "C1", "C2"]] = None


class CMRAScore(BaseModel):
    CMRARawScore: Optional[int] = None
    CMRAPercentile: Optional[int] = None


class CognifyScore(BaseModel):
    CognifyPercentile: Optional[int] = None
    CognifyProblemSolvingPercentile: Optional[int] = None
    CognifyNumericalReasoningPercentile: Optional[int] = None
    CognifyVerbalKnowledgePercentile: Optional[int] = None


class CPIScore(BaseModel):
    CPIAgreeableness: Optional[int] = None
    CPIConscientiousness: Optional[int] = None
    CPIExtraversion: Optional[int] = None
    CPIOpenness: Optional[int] = None
    CPIStability: Optional[int] = None
    CPICooperation: Optional[int] = None
    CPISelflessness: Optional[int] = None
    CPIAchievement: Optional[int] = None
    CPIDependability: Optional[int] = None
    CPIAssertiveness: Optional[int] = None
    CPISociability: Optional[int] = None
    CPIImagination: Optional[int] = None
    CPIIntellect: Optional[int] = None
    CPIEvenTemperament: Optional[int] = None
    CPISelfConfidence: Optional[int] = None


class CSAPScore(BaseModel):
    CSAPRecommendation: Optional[Literal["Not Recommended", "Recommended", "Highly Recommended"]] = None
    CSAPSalesDisposition: Optional[int] = None
    CSAPColdCalling: Optional[int] = None
    CSAPSalesClosing: Optional[int] = None
    CSAPAchievement: Optional[int] = None
    CSAPMotivation: Optional[int] = None
    CSAPCompetitiveness: Optional[int] = None
    CSAPGoalOrientation: Optional[int] = None
    CSAPPlanning: Optional[int] = None
    CSAPInitiative: Optional[int] = None
    CSAPTeamPlayer: Optional[int] = None
    CSAPManagerial: Optional[int] = None
    CSAPAssertiveness: Optional[int] = None
    CSAPPersonalDiplomacy: Optional[int] = None
    CSAPExtraversion: Optional[int] = None
    CSAPCooperativeness: Optional[int] = None
    CSAPRelaxedStyle: Optional[int] = None
    CSAPPatience: Optional[int] = None
    CSAPSelfConfidence: Optional[int] = None
    CSAPInvalid: Optional[bool] = None
    CSAPInconsistency: Optional[int] = None


class EmotifyScore(BaseModel):
    EmotifyPercentile: Optional[int] = None
    EmotifyPerceivingPercentile: Optional[int] = None
    EmotifyUnderstandPercentile: Optional[int] = None
    EmotifyManagingPercentile: Optional[int] = None


class EPPScore(BaseModel):
    EPPPercentMatch: Optional[int] = None
    EPPInvalid: Optional[bool] = None
    EPPInconsistency: Optional[int] = None
    Accounting: Optional[int] = None
    AdminAsst: Optional[int] = None
    Analyst: Optional[int] = None
    BankTeller: Optional[int] = None
    Collections: Optional[int] = None
    CustomerService: Optional[int] = None
    FrontDesk: Optional[int] = None
    Manager: Optional[int] = None
    MedicalAsst: Optional[int] = None
    Production: Optional[int] = None
    Programmer: Optional[int] = None
    Sales: Optional[int] = None
    EPPAchievement: Optional[int] = None
    EPPMotivation: Optional[int] = None
    EPPCompetitiveness: Optional[int] = None
    EPPManagerial: Optional[int] = None
    EPPAssertiveness: Optional[int] = None
    EPPExtraversion: Optional[int] = None
    EPPCooperativeness: Optional[int] = None
    EPPPatience: Optional[int] = None
    EPPSelfConfidence: Optional[int] = None
    EPPConscientiousness: Optional[int] = None
    EPPOpenness: Optional[int] = None
    EPPStressTolerance: Optional[int] = None


class Excel16Score(BaseModel):
    Excel16RawScore: Optional[int] = None
    Excel16Percentile: Optional[int] = None


class Excel365Score(BaseModel):
    Excel365Score: Optional[int] = None
    Excel365Proficiency: Optional[Literal["Beginner", "Foundational", "Intermediate", "Skilled", "Advanced"]] = None


class GAMERScore(BaseModel):
    GAMERawScore: Optional[int] = None
    GAMEPercentile: Optional[int] = None
    GAMENumericalReasoningPercentile: Optional[int] = None
    GAMEVerbalAbilityPercentile: Optional[int] = None
    GAMEAttentionToDetailPercentile: Optional[int] = None


class IllustratScore(BaseModel):
    IllustraitPercentile: Optional[int] = None
    IllustraitInvalid: Optional[int] = None
    IllustraitInconsistency: Optional[int] = None
    IllustraitCompetencies: Optional[Dict[str, int]] = None


class MRABScore(BaseModel):
    MRABPercentile: Optional[int] = None
    MRABAttention: Optional[int] = None
    MRABMemory: Optional[int] = None
    MRABReasoning: Optional[int] = None
    MRABDividedAttention: Optional[int] = None
    MRABVigilance: Optional[int] = None
    MRABFiltering: Optional[int] = None
    MRABVisualization: Optional[int] = None
    MRABVerbalWorkingMemory: Optional[int] = None
    MRABSpatialWorkingMemory: Optional[int] = None
    MRABLogic: Optional[int] = None
    MRABInformationOrdering: Optional[int] = None
    MRABPerceptualReconstruction: Optional[int] = None


class PPT16Score(BaseModel):
    PPT16RawScore: Optional[int] = None
    PPT16Percentile: Optional[int] = None


class PPT365Score(BaseModel):
    PPT365Score: Optional[int] = None
    PPT365Proficiency: Optional[Literal["Beginner", "Foundational", "Intermediate", "Skilled", "Advanced"]] = None


class SalesAPScore(BaseModel):
    SalesAPRecommendation: Optional[Literal["Not Recommended", "Recommended", "Highly Recommended"]] = None
    SalesAPSalesDisposition: Optional[int] = None
    SalesAPColdCalling: Optional[int] = None
    SalesAPSalesClosing: Optional[int] = None
    SalesAPAchievement: Optional[int] = None
    SalesAPMotivation: Optional[int] = None
    SalesAPCompetitiveness: Optional[int] = None
    SalesAPGoalOrientation: Optional[int] = None
    SalesAPPlanning: Optional[int] = None
    SalesAPInitiative: Optional[int] = None
    SalesAPTeamPlayer: Optional[int] = None
    SalesAPManagerial: Optional[int] = None
    SalesAPAssertiveness: Optional[int] = None
    SalesAPPersonalDiplomacy: Optional[int] = None
    SalesAPExtraversion: Optional[int] = None
    SalesAPCooperativeness: Optional[int] = None
    SalesAPRelaxedStyle: Optional[int] = None
    SalesAPPatience: Optional[int] = None
    SalesAPSelfConfidence: Optional[int] = None
    SalesAPInvalid: Optional[bool] = None
    SalesAPInconsistency: Optional[int] = None


class TTScore(BaseModel):
    TTWordsPerMinute: Optional[int] = None
    TTNumberOfErrors: Optional[int] = None
    TTPercentile: Optional[int] = None


class TenKeyScore(BaseModel):
    TenKeyKeystrokes: Optional[int] = None
    TenKeyAccuracy: Optional[str] = None


class UCATScore(BaseModel):
    UCATRawScore: Optional[int] = None
    UCATPercentile: Optional[int] = None
    UCATMathPercentile: Optional[int] = None
    UCATSpatialPercentile: Optional[int] = None
    UCATDetailPercentile: Optional[int] = None
    UCATLogicPercentile: Optional[int] = None


class WAAScore(BaseModel):
    WAAPercentile: Optional[int] = None


class Word16Score(BaseModel):
    Word16RawScore: Optional[int] = None
    Word16Percentile: Optional[int] = None


class Word365Score(BaseModel):
    Word365Score: Optional[int] = None
    Word365Proficiency: Optional[Literal["Beginner", "Foundational", "Intermediate", "Skilled", "Advanced"]] = None


class WPPScore(BaseModel):
    WPPRecommendation: Optional[Literal["Low", "Medium", "High"]] = None
    WPPConscientiousness: Optional[int] = None
    WPPPerseverance: Optional[int] = None
    WPPHonesty: Optional[int] = None
    WPPTheft: Optional[int] = None
    WPPInvalid: Optional[bool] = None
    WPPFaking: Optional[int] = None


class WSPScore(BaseModel):
    WSPPercentile: Optional[int] = None
    WSPSafetyPercentile: Optional[int] = None
    WSPRiskPercentile: Optional[int] = None
    WSPStressPercentile: Optional[int] = None
    WSPDrugPercentile: Optional[int] = None
    WSPViolencePercentile: Optional[int] = None
    WSPInvalid: Optional[int] = None
    WSPValidityENHPercentile: Optional[int] = None
    WSPValidityINCScore: Optional[int] = None


class WTMAScore(BaseModel):
    WTMARawScore: Optional[int] = None
    WTMAPercentile: Optional[int] = None


class TestMakerScore(BaseModel):
    TMXXRawScore: Optional[int] = None
    TMXXPercentile: Optional[int] = None
    TMXXTimeTaken: Optional[int] = None
    TMXXWordsPerMinute: Optional[int] = None
    TMXXAdjustedWordsPerMinute: Optional[int] = None
    TMXXNumberOfErrors: Optional[int] = None


class CombinedScore(
    RankingScore,
    CASTScore,
    CBSTScore,
    CCATScore,
    CLIKScore,
    CLPTEnglishScore,
    CMRAScore,
    CognifyScore,
    CPIScore,
    CSAPScore,
    EmotifyScore,
    EPPScore,
    Excel16Score,
    Excel365Score,
    GAMERScore,
    IllustratScore,
    MRABScore,
    PPT16Score,
    PPT365Score,
    SalesAPScore,
    TTScore,
    TenKeyScore,
    UCATScore,
    WAAScore,
    Word16Score,
    Word365Score,
    WPPScore,
    WSPScore,
    WTMAScore,
    TestMakerScore,
):
    pass


class ScoresCandidate(Candidate):
    date: datetime
    eventId: str
    testTakerId: int


class GetScoresResponse(BaseModel):
    orderId: str
    externalId: Optional[str] = None
    candidate: ScoresCandidate
    scores: Optional[CombinedScore] = None
    reportUrl: HttpUrl
    candidateReportUrl: Optional[str] = None
    metAllScoreRanges: Literal["Yes", "No", "N/A"] = "N/A"


def get_grouped_fields_by_parent[T: BaseModel](combined_score: CombinedScore) -> List[T]:
    grouped_fields = []
    combined_score_dict = combined_score.model_dump()

    for base_class in combined_score.__class__.__bases__:
        if issubclass(base_class, BaseModel) and base_class is not BaseModel:
            fields = {i: combined_score_dict.get(i) for i in base_class.model_fields.keys()}
            grouped_fields.append(base_class(**fields))

    return grouped_fields
