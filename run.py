from turtle import pd
from apply import Applier


patient_id = "30"
pd_id = "4"


applier = Applier(base='https://api.logicahealth.org/FerociousCilantro/open')
applier.create_careplan(pd_id, patient_id)
