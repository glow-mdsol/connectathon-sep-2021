from turtle import pd
from apply import Applier


patient_id = "SMART-1081332"
pd_id = "17293"


applier = Applier()
applier.create_careplan(pd_id, patient_id)
