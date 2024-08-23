# Student CSM Ingestion

# Table of Contents
- [Student CSM Ingestion](#student-csm-ingestion)
- [Table of Contents](#table-of-contents)
  - [Description](#description)
  - [Architecture](#architecture)

<a id="description"></a>
## Description
This process runs once a day and ingests student data into Symplicity CSM. It does the following actions
 - Creates students not in CSM that are in Started Program Pathway or Alumni status
 - Disables students that are active in CSM and are no longer in SPP or Alumni Status
 - Updates student demographic data if any changes are found


<a id="architecture"></a>
## Architecture
 - ECR: https://us-west-2.console.aws.amazon.com/ecr/repositories/private/523292522460/symplicity_student_ingestion?region=us-west-2
 - ECS

