from pydantic import BaseModel


class CVLinks(BaseModel):
    github: str = ""
    linkedin: str = ""
    website: str = ""


class CVBasics(BaseModel):
    name: str
    title: str
    summary: str
    location: str
    email: str
    phone: str
    links: CVLinks


class CVExperience(BaseModel):
    company: str
    role: str
    location: str
    startDate: str
    endDate: str | None = None
    highlights: list[str]


class CVEducation(BaseModel):
    institution: str
    degree: str
    startDate: str
    endDate: str


class CVSkillGroup(BaseModel):
    category: str
    items: list[str]


class CVCertification(BaseModel):
    name: str
    issuer: str
    date: str = ""


class CVLanguage(BaseModel):
    name: str
    level: str


class CVData(BaseModel):
    basics: CVBasics
    experience: list[CVExperience]
    education: list[CVEducation]
    skills: list[CVSkillGroup]
    certifications: list[CVCertification]
    languages: list[CVLanguage]
    softSkills: list[str]


class CVUploadPreview(BaseModel):
    en: CVData | None = None
    fr: CVData | None = None
    fa: CVData | None = None
    translation_errors: list[str] = []
