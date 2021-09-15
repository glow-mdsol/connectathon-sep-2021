

from apply import Applier
from fhir.resources.careplan import CarePlan

def test_create_careplan():
    patient_id = "SMART-1081332"
    pd_id = "16985"
    applier = Applier()
    cp = applier.create_careplan(pd_id, patient_id)
    assert isinstance(cp, (CarePlan, ))

