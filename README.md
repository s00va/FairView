# FairView
F@irView is a prototype digital system designed to manage talk submissions and reviews for industry conferences in a fair, transparent, and anonymous manner. It helps conference managers, speakers, and reviewers handle the complete lifecycle of talk selection — from submission to feedback — while ensuring unbiased and structured evaluation.


Key Features
- Conference Management: Set the number of speaking slots, submission deadlines, and manage user registrations.
- Anonymous Review Process: Automatically assigns talks to reviewers, anonymizes submissions, and prevents conflicts of affiliation.
- Reviewer Scoring: Reviewers provide a score (1–10) and short textual feedback for each talk.
- Automated Ranking: Generates a ranked list of talks based on average scores and allocates slots to top-ranked talks, resolving ties randomly.
- Feedback Reports: Compiles reviewer comments into reports for applicants without revealing scores.


User Roles:
- Conference Manager: Full access to all submissions, reviewers, and results.
- Applicants & Reviewers: Access limited to tasks relevant to their role, minimizing bias.
- Communication: Built-in forum for questions to the Conference Manager.

Project Structure
- Developed using object-oriented programming principles.
- Modular and well-documented code to support collaboration and maintainability.
- Includes scripts and data files required to run the prototype locally.

# How To Install
Clone the repository:
`git clone https://github.com/s00va/FairView.git`

# How To Run
cd into `FairView` directory. \
Run: `uv run ./main.py`

# To Generate Example Data
Run `uv run ./example_data.py -h` - This will show what actions can occur.\
EXAMPLES:\
`uv run .\example_data.py -s 10 -r 10 -cm 10` - Generates 10 speaker, 10 review and 10 conference manager accounts.\
`uv run .\example_data.py -c 20` - Generates 20 conferences across all conference manager accounts.\
`uv run .\example_data.py -js 5 -cid 12` - Joins 5 speakers to the conference with id 12 (You can view the ID in the url when at `manage-conference/<id>`)\
`uv run .\example_data.py -jr 11 -cid 3` - Joins 11 reviewers to the conference with id 3\
`uv run .\example_data.py -cid 12 -t 100` - Creates 100 talks over all speakers which have joined conference 12.  
`uv run .\example_data.py -rt -cid 12` - Automatically review every unreviewed item in the conference of id 12. MAKE SURE TO HAVE ALLOCATED REVIEWS AS THE CONFERENCE MANAGER FIRST!

# Features Not Implemented
- Prevent joining conferences when Status is NOT open.
- Automatic changing of status when submission deadline is met.
- More secure method for speakers and reviewers to join conferences.
- Conference manager page show all speakers and reviews which have joined the conference.
- Conference manager page show all on going talks and reviews before final talk results.
- View account information.
- Edit account information.
- Edit talk before submission deadline.
- Edit reviews.
- Edit conference details.
- Speaker page to view details of talks.
- Speaker should see if their talk was accepted/rejected on a tie. (Infrastructure exists already)
- Search and filter capabilities for all tables.

