## dakota

Dakota was developed as a curation and QA framework that can automate data processing for a variety of general tasks. With an Excel file, the customer specifies processing steps and provides any supporting data tables needed. Back-end computations are performed by interpreting the Excel directives and providing access to a subset of the Python language. The user specifies all processing steps and any supporting data tables directly within a required Excel file. The Excel file will not be published or described here.

The use case for this software development was to automate a variety of processes necessary for an accounting team to produce weekly and monthly reports. The previous solution, relying on VBA, was clunky and difficult to maintain. Using python and pandas, the process is more efficient and transparent.

The result? A user-friendly interface that can 1) be run completely in-house and 2) allows modification of supporting data and/or computation processes without touching the back-end code base.