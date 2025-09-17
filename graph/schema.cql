-- Organisation
CREATE NODE TABLE Organisation (
    org_id INT64,
    org_name STRING,
    org_type STRING,
    org_function STRING,
    PRIMARY KEY(org_id)
);

-- Stakeholders
CREATE NODE TABLE Stakeholder (
    stakeholder_id INT64,
    org_id INT64,
    name STRING,
    job_title STRING,
    role STRING,
    PRIMARY KEY(stakeholder_id)
);

-- Pain points
CREATE NODE TABLE PainPoint (
    painpoint_id INT64,
    org_id INT64,
    description STRING,
    severity STRING,
    urgency STRING,
    PRIMARY KEY(painpoint_id)
);

-- Commercial routes
CREATE NODE TABLE Commercial (
    commercial_id INT64,
    org_id INT64,
    method STRING,
    budget DOUBLE,
    PRIMARY KEY(commercial_id)
);

-- Org-to-Org relationships (mission, supplier, consumer, oversight)
CREATE REL TABLE OrgRelation (
    FROM Organisation TO Organisation,
    relationship_type STRING
);

-- Subclass links back to Organisation
CREATE REL TABLE HasStakeholder (FROM Organisation TO Stakeholder);
CREATE REL TABLE HasPainPoint (FROM Organisation TO PainPoint);
CREATE REL TABLE ProcuresThrough (FROM Organisation TO Commercial);