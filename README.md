# September Connectathon Code

This is a little bit of python intended to build out a framework to replicate the function of the `$apply` capability in CDS Hooks

It provides a shell which we can build upon and will aid in what we need for the Schedule of Activity work.

# Modelling assumptions
* Whereever practical use PATCH/UPSERT semantics for resources.  
* A consistent naming/version system should be used to indicate changes for the study, either through a large change (like a Protocol Amendment) or smaller changes (such as new study configuration).  
* A valid `ResearchStudy` shall be created and included in any and all `Bundles`.  The `ResearchStudy` should include all information making it possible to find and identify the study  through the use of common declared identifiers (eg ClinicalTrials.gov identifier, external identifiers for the study/intervention, internal identifiers for the study/intervention)
* 
* Any decomposable activity is implemented using a `PlanDefinition` resource (eg Schedule of Activities, Visit, Vital Signs Assessment)
* Any activity that corresponds to an executable action, is implemented as an `ActivityDefinition` (eg Record Visit Date, Take Systolic Blood Pressure assessment, Individual Lab test)
* Composite activities are created using the `PlanDefinition.action` attribute (Array), with the child activities will be ordered in expected sequence of operation (eg Record Visit Date -> Perform Vital Signs -> Perform ECG Assessment)
  * If timing/offset is known for sibling elements, a trigger element will be assigned a identifier and the `relatedAction.actionId` on the reference will be used to link to the triggering element/activity (with the `relatedAction.relationship` attribute)
* We have not modelled using any preferred vocabulary/terminology, but would recommend that terminology used should be internationally recognised and used (eg SNOMED-CT, LOINC)

# Implementation Artifactds
* When a Patient is enrolled in the study, a `ResearchSubject` resource will be created (via a POST) with a reference to `Patient` through the `individual` attribute and the `ResearchStudy` through the `study` attribute.


## Process of implementation
* In the current approach

