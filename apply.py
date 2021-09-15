import json
import requests
from fhir.resources.plandefinition import PlanDefinition
from fhir.resources.activitydefinition import ActivityDefinition
from fhir.resources.careplan import CarePlan
from fhir.resources.researchstudy import ResearchStudy
from fhir.resources.researchsubject import ResearchSubject
from fhir.resources.servicerequest import ServiceRequest
from fhir.resources.operationoutcome import OperationOutcome
from fhir.resources.patient import Patient
from fhir.resources.reference import Reference

class Applier:

    def __init__(self, base='https://api.logicahealth.org/terribleLizard/open'):
        self._endpoint = base
        self._client = requests.Session()

    def create_subject(self, research_subject_id, patient_id, research_study_id):
        _rs = self._client.get(f"{self._endpoint}/ResearchStudy/{research_study_id}")
        if _rs.status_code != 200:
            raise ValueError("ResearchStudy not found")
        rs = ResearchStudy(**_rs.json())
        _pt = self._client.get(f"{self._endpoint}/Patient/{patient_id}")
        if _pt.status_code != 200:
            raise ValueError("Patient not found")
        pt = Patient(**_pt.json)
        rs = ResearchSubject()
        rs.study = Reference(rs)
        rs.individual = Reference(pt)
    
    def create_careplan(self, plan_definition_id, patient_id):
        _pd = self._client.get(f"{self._endpoint}/PlanDefinition/{plan_definition_id}")
        if _pd.status_code != 200:
            raise ValueError("Unable to load PlanDefinition", _pd.content)
        pd = PlanDefinition(**_pd.json())
        _sb = self._client.get(f"{self._endpoint}/Patient/{patient_id}")
        if _sb.status_code != 200:
            raise ValueError("Unable to load Patient")
        sb = Patient(**_sb.json())
        cp = CarePlan(intent="plan", status="active", subject=Reference(reference=f"Patient/{sb.id}", display=sb.name[0].text))
        cp.instantiatesCanonical = [f"PlanDefinition/{pd.id}"]
        children = []
        for action in pd.action:
            print(f"Accessing: {action.definitionUri}")
            _rs = self._client.get(f"{self._endpoint}/{action.definitionUri}")
            # Issue - need to be able to resolve definitionUri to CanonicalUri
            # - this may be down to how we are loading in the data, using defintionUri rather than canonical
            if 'error' in _rs.json():
                continue
            resource = _rs.json()
            if resource['resourceType'] == "ActivityDefinition":
                ad = ActivityDefinition(**resource)
                print(f"Creating ServiceRequest for {action.definitionUri}")
                sr = self.create_servicerequest(activity_definition_id=ad.id, 
                    patient_id=patient_id)
                if not cp.activity:
                    cp.activity = []
                cp.activity.append(dict(reference=Reference(reference=f"ServiceRequest/{sr.id}"), 
                    detail=dict(status="scheduled",
                    kind="ServiceRequest", 
                    instantiatesCanonical=[f"ActivityDefinition/{ad.id}"])))
            elif resource['resourceType'] == "PlanDefinition":
                print(f"Creating CarePlan for {action.definitionUri}")
                _cp = self.create_careplan(action.definitionUri.split("/")[-1], patient_id)
                children.append(_cp)
            else:
                print("Can't process", resource)
                continue
        with open(f'cp_{plan_definition_id}.json', 'w') as fh:
            fh.write(cp.json())
        pcap = self._client.post(f"{self._endpoint}/CarePlan", json=json.loads(cp.json()))
        if 200 <= pcap.status_code < 300:
            pcp = CarePlan(**pcap.json()) 
            print(f"Created CarePlan {pcp.id}")
            child: CarePlan
            for child in children:
                if not child.partOf:
                    child.partOf = []
                child.partOf.append(f"CarePlan/{pcp.id}") 
                cc = self._client.post(f"{self._endpoint}/CarePlan", json=json.loads(child.json()))
        else:
            raise ValueError("Error creating CarePlan", pcap.content)
        return pcp

    def create_servicerequest(self, activity_definition_id, patient_id):
        _ad = self._client.get(f"{self._endpoint}/ActivityDefinition/{activity_definition_id}")
        if _ad.status_code != 200:
            raise ValueError("ActivityDefinition not found", _ad.content)
        ad = ActivityDefinition(**_ad.json())
        _sb = self._client.get(f"{self._endpoint}/Patient/{patient_id}")
        if _sb.status_code != 200:
            raise ValueError("Unable to load PlanDefinition")
        sb = Patient(**_sb.json())
        sr = ServiceRequest(intent="plan", status="active", subject=Reference(reference=f"Patient/{sb.id}"))
        sr.instantiatesCanonical = [f"ActivityDefinition/{ad.id}"]
        with open('sr.json', 'w') as srh:
            srh.write(sr.json())
        outcome = self._client.post(f"{self._endpoint}/ServiceRequest", json=json.loads(sr.json()))
        if 200 <= outcome.status_code <= 299:
            _sri = ServiceRequest(**outcome.json())
            print(f"Created ServiceRequest {_sri.id}")
        else:
            _op = OperationOutcome(**outcome.json())
            raise ValueError("Error: ", _op)
        return _sri


    def apply(self, plan_definition_id, subject_id):
        _pd = self._client.get(f"{self._endpoint}/PlanDefinition/{plan_definition_id}")
        if _pd.status_code != 200:
            raise ValueError("Unable to retrieve PlanDefinition")
        
        pd = PlanDefinition(**_pd.json())
        # for each action
        for action in pd.action:
            if action.fhir_type_name() == "PlanDefinition":
                self.create_careplan(plan_definition_id=action.definitionUri)
            elif action.fhir_type_name() == "ActivityDefinition":
                self.create_servicerequest(activity_definition_uri=action.definitionUri)
        