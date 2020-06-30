#!/usr/bin/python 

import json
import os
import sys
import logging
import requests
import shutil
from git import Repo
from pathlib import Path
import csv
import argparse


def check_repository_status(repo_name):
    """
    check whether the repository exists in user's account
    :return: available - if requested repository exits
    error_code - if repository not exists
  """
    url = _filetrek_url + repo_name
    try:
        response = requests.get(url=url, headers=_headers)
        if response.status_code != 200:
            logging.info("==> The given repository not exists due to error code - %s and reason - %s",
                         response.status_code, response.reason)
            return response.reason

        logging.info("The given repository - %s exists in the user's account", repo_name)
        return "available"
    except Exception as e:
        logging.info("==> HTTP Exception : " + str(e))
        print_exception_details(e)
        sys.exit(1)


def check_branch_existence(repo_name, branch_name):
    """
    Check whether a branch already exists in the repository in the name of new branch requested
    :return: True - if branch exists, False - if branch not exists
  """
    logging.debug("CHECKING WHETHER BRANCH - %s IS ALREADY EXISTING IN THE REPOSITORY - %s", branch_name, repo_name)

    # HTTP url to access the get a specific branch endpoint of GitHub API
    url = _filetrek_url + repo_name + "/branches/" + branch_name

    try:
        response = requests.get(url=url, headers=_headers)
        if response.status_code != 200 and response.status_code != 404:
            logging.info("==> HTTP Request to check branch existence failed with Error code - %s and reason - %s",
                         response.status_code, response.json()['message'])
            sys.exit(1)

        if "message" in response.json() and response.json()['message'] == "Branch not found":
            logging.info("==> Branch - %s NOT EXISTS in the given repository - %s", branch_name, repo_name)
            return False

        logging.info("Branch - %s EXISTS in the given repository - %s", branch_name, repo_name)
        return True

    except Exception as e:
        logging.info("==> HTTP Exception : " + str(e))
        print_exception_details(e)
        sys.exit(1)


def create_branch_from_existing_branch(repo_name, src_branch, new_branch):
    """
    creates a new branch from an existing branch in the given repository.
    To create a new branch, it requires SHA of the an existing branch and name of the new branch
    :return: nothing
  """
    logging.debug("CREATING A NEW BRANCH - %s FROM AN EXISTING BRANCH - %s", new_branch, src_branch)

    # HTTP url to access the branch creation endpoint of GitHub API
    url = _filetrek_url + repo_name + "/git/refs"

    # Fetch the SHA of the source branch using the get_sha_source_branch method
    sha_src_branch = get_sha_source_branch(repo_name, src_branch)

    # Data to be sent in the HTTPS POST Request to create new branch
    data = {"sha": sha_src_branch, "ref": "refs/heads/" + new_branch}
    payload = json.dumps(data)

    try:
        response = requests.post(url, data=payload, headers=_headers)
        if response.status_code != 201:
            logging.info("==> The HTTPS Post request to create a new branch failed with status %s and reason is %s",
                         response.status_code, response.text)
            sys.exit(1)

        logging.info("New Branch with name %s has been created ", new_branch)
        logging.debug("New Branch Details : " + str(response.json()))

    except Exception as e:
        logging.info("==> HTTPS Exception : " + str(e))
        print_exception_details(e)
        sys.exit(1)


def get_sha_source_branch_from_refs(repo_name, src_branch):
    """
    Fetch the SHA of the source branch and return the SHA of the source branch
    :return: SHA of the branch
  """

    # HTTP URL to access the get references endpoint of GitHub API
    url = _filetrek_url + repo_name + "/git/refs"

    source_branch_name = 'refs/heads/' + src_branch
    sha_source_branch = ''

    # If response is 200, check whether source branch reference exists on response json.
    # If exists, then retrieve the sha of the source branch from the json

    try:
        response = requests.get(url, headers=_headers)

        if response.status_code != 200:
            logging.info("==> Unable to fetch the SHA of the given branch %s due to error code- %s and reason - %s",
                         src_branch, response.status_code, response.json()['message'])
            sys.exit(1)

        for x in response.json():
            print(x['ref'])
            if x['ref'] == source_branch_name:
                logging.debug("Source %s exists in the given repository ", x['ref'])
                sha_source_branch = x['object']['sha']
                logging.debug("SHA of the Source Branch : " + sha_source_branch)
                break

        if sha_source_branch == '':
            logging.info("Error is retrieving the SHA of the source branch - " + src_branch)
            logging.info(response.content)
            sys.exit(1)

        return sha_source_branch

    except Exception as e:
        logging.info("==> HTTP Exception : " + str(e))
        print_exception_details(e)
        sys.exit(1)


def get_sha_source_branch(repo_name, src_branch):
    """
    Fetch the SHA of the source branch and return the SHA of the source branch
    :return: SHA of the branch
  """

    # HTTP URL to access the get branch endpoint of GitHub API
    url = _filetrek_url + repo_name + "/branches/" + src_branch
    sha_source_branch = ''

    # If response is 200, check whether source branch  exists on response json.
    # if exists, then retrieve the sha of the source branch from the json

    try:
        response = requests.get(url, headers=_headers)
        if response.status_code != 200:
            logging.info("==> Unable to fetch the SHA of the given branch %s due to error code- %s and reason - %s",
                         src_branch, response.status_code, response.json()['message'])
            sys.exit(1)

        sha_source_branch = response.json()['commit']['sha']
        logging.debug("SHA of the Source Branch : " + sha_source_branch)

        if sha_source_branch == '':
            logging.info("Error is retrieving the SHA of the source branch - " + src_branch)
            logging.info(response.content)
            sys.exit(1)

        return sha_source_branch
    except Exception as e:
        logging.info("==> HTTP Exception : " + str(e))
        print_exception_details(e)
        sys.exit(1)


def get_default_branch_status(repo_name, src_branch, new_branch):
    """
    Retrieve the name of the default branch of the given repository
    :return: update - if default branch is not the new branch
    no update - if default branch is the new branch
  """
    logging.debug("FETCHING THE CURRENT DEFAULT BRANCH OF THE REPOSITORY - %s ", repo_name)

    print("Getting the default branch")

    url = _filetrek_url + repo_name

    try:
        response = requests.get(url=url, headers=_headers)
        if response.status_code != 200:
            logging.info("==> Unable to fetch the default branch of repository %s due to error code- %s and reason"
                         " - %s", src_branch, response.status_code, response.json()['message'])
            sys.exit(1)

        logging.info(" Current Default Branch of the repository - %s is %s", repo_name,
                     response.json()['default_branch'])

        if response.json()['default_branch'] == new_branch:
            logging.info("The default branch is - %s as expected", new_branch)
            return "needs no update"
        else:
            logging.info("==> The default branch should be set to new branch- %s", new_branch)
            return "update"

    except Exception as e:
        logging.info("==> HTTP Exception : " + str(e))
        print_exception_details(e)
        sys.exit(1)


def update_default_branch(repo_name, new_branch):
    """
    Update the default branch of the given repository to the new branch
    :return: nothing
  """
    logging.debug("UPDATING THE DEFAULT BRANCH OF THE REPOSITORY TO- %s ", new_branch)

    url = _filetrek_url + repo_name

    data = {"name": repo_name, "default_branch": new_branch}

    payload = json.dumps(data)
    try:
        response = requests.patch(url=url, data=payload, headers=_headers)
        logging.info("Updated Current Default Branch of the repository - %s is %s", repo_name,
                     response.json()['default_branch'])
    except Exception as e:
        logging.info("==> HTTP Exception : " + str(e))
        print_exception_details(e)
        sys.exit(1)


def remove_branch_protection(repo_name, new_branch):
    """
    removes the protection of the branch and also its corresponding protection rules
    :return: nothing
  """
    logging.debug("Removing the branch protection for the branch - %s", new_branch)
    url = _filetrek_url + repo_name + "/branches/" + new_branch + "/protection"

    try:
        response = requests.delete(url=url, headers=_headers)
        if response.status_code != 204:
            logging.info("Unable to remove the branch protection rules for the branch - %s due to error - %s and"
                         " reason -%s", new_branch, response.status_code, response.reason)
            sys.exit()

        logging.info("Removed branch protection for the branch - %s", new_branch)
    except Exception as e:
        logging.info("==> HTTP Exception : " + str(e))
        print_exception_details(e)
        sys.exit(1)


def set_and_update_branch_protection(repo_name, new_branch):
    """
    en`ables the protection for the new branch and also set the protection rules for the branch
    :return: nothing
  """
    logging.debug("ENABLING AND UPDATING THE BRANCH PROTECTION RULES FOR THE BRANCH - %s", new_branch)
    url = _filetrek_url + repo_name + "/branches/" + new_branch + "/protection"
    headers = {'Authorization': _authorization_token, 'Accept': 'application/vnd.github.luke-cage-preview+json'}
    data = {
        "required_status_checks": None,
        "enforce_admins": True,
        "required_pull_request_reviews":
            {
                "dismiss_stale_reviews": False,
                "require_code_owner_reviews": False,
                "required_approving_review_count": 1
            },
        "restrictions": None
    }

    try:
        response = requests.put(url=url, headers=headers, data=json.dumps(data))
        if response.status_code != 200:
            logging.info("==> Enable and Update branch protection rules for the branch - %s failed due to error code"
                         " - %s and reason - %s", new_branch, response.status_code, response.reason)
            sys.exit(1)

        logging.info("Enabled and Updated branch protection rules for the branch - %s", new_branch)
    except Exception as e:
        logging.info("==> HTTP Exception : " + str(e))
        print_exception_details(e)
        sys.exit(1)


def get_branch_protection_rules(repo_name, new_branch):
    """
    retrieves the branch protection rules status(in json) of the new branch and compares  with expected status json
    :return: a string [1. Configured as expected (if status is as expected)
    2. Not configured as expected (if status is not as expected)]
    3. Branch not protected (if branch doesn't have any protection rules)
  """
    logging.debug("FETCHING THE Branch protection rules of the branch - %s ", new_branch)
    url = _filetrek_url + repo_name + "/branches/" + new_branch + "/protection"
    headers = {'Authorization': _authorization_token, 'Accept': 'application/vnd.github.luke-cage-preview+json'}

    expected_branch_protection_rules = {
        'url': url,
        'required_pull_request_reviews': {
            'url': url + "/required_pull_request_reviews",
            'dismiss_stale_reviews': False,
            'require_code_owner_reviews': False,
            'required_approving_review_count': 1
        }, 'enforce_admins': {
            'url': 'https://api.github.com/repos/FileTrek/' + repo_name + '/branches/'
                   + new_branch + '/protection/enforce_admins', 'enabled': True
        }
    }

    try:
        response = requests.get(url=url, headers=headers)
        if response.status_code != 200 and response.status_code != 404:
            logging.info("==> Unable to retrieve the branch protection rules for branch %s due to error - %s and"
                         " reason - %s", new_branch, response.status_code, response.json()['message'])
            sys.exit(1)

        if "message" in response.json() and response.json()['message'] == 'Branch not protected':
            logging.info("==> The branch %s is not branch protected - Needs update", new_branch)
            return "Branch not protected"

        if expected_branch_protection_rules == response.json():
            logging.info("The branch - %s is protected and configured as expected", new_branch)
            return "Configured as expected"

        logging.info("==> The branch - %s is protected but not configured as expected", new_branch)
        logging.info("Current Branch Protection rules are - " + str(response.json()))
        logging.info("Expected Protection rules are %s ", expected_branch_protection_rules)
        return "Not configured as expected"

    except Exception as e:
        logging.info("==> HTTP Exception : " + str(e))
        print_exception_details(e)
        sys.exit(1)


def verify_branch_setup(args):
    """
    logs the status of repository, source branch, new branch - their existence, commit difference between the source
    and the new branch
    :return: nothing
  """

    # check whether source and new branch name is same
    if args.srcbranch == args.newbranch:
        logging.info("==> The source branch name and new branch name cannot be same. Try with unique branch names")
        sys.exit(1)

    # configuring the verify mode
    logging.info("Entering verify Mode")

    repository_status = check_repository_status(args.reponame)
    if repository_status is not "available":
        logging.info("==> The given repository is  - %s. Try with a valid Repository", repository_status)
        sys.exit(1)

    source_branch_existence_status = check_branch_existence(args.reponame, args.srcbranch)
    new_branch_existence_status = check_branch_existence(args.reponame, args.newbranch)

    if source_branch_existence_status is False:
        logging.info("WARN: Source branch - %s doesn't exist", args.srcbranch)

    if source_branch_existence_status is True and new_branch_existence_status is False:
        logging.info("Source branch - %s exists and there is no branch in the repository named - %s",
                     args.srcbranch, args.newbranch)
        logging.info("==> Allowed to Perform - "
                     "1. New branch creation\n"
                     "2. Branch protection configuration for new branch\n"
                     "3. Updating default branch to new branch")
        sys.exit(1)

    if source_branch_existence_status is True and new_branch_existence_status is True:
        logging.info("Allowed to Perform below actions based on the status of the new branch -  \n"
                     "1. Check and update default branch of the repository\n"
                     "2. Check and update the branch protection rules\n")

        set_diff_commit = branches_commit_difference(args.reponame, args.srcbranch, args.newbranch)
        default_branch_status = get_default_branch_status(args.reponame, args.srcbranch, args.newbranch)
        branch_protection_status = get_branch_protection_rules(args.reponame, args.newbranch)

        if set_diff_commit is not None and len(set_diff_commit) != 0:
            get_commit_details(args.reponame, set_diff_commit)

        if not (branch_protection_status == 'Configured as expected'):
            logging.info("==> The Protection rules of the new branch is not configured as expected")
            sys.exit(1)


def setup_new_branch(args):
    """
      create a new brnach and configure it or change the status of repository, source branch, new branch to the
      expected state based on their current state
      :return: nothing
    """

    try:
        # check whether source and new branch name is same
        if args.srcbranch == args.newbranch:
            logging.info("==> The source branch name and new branch name cannot be same. Try with unique branch names")
            sys.exit(1)

        # configuring the update mode
        logging.info("Entering Create / Update Mode")

        repository_status = check_repository_status(args.reponame)
        if repository_status is not "available":
            logging.info("==> The given repository is  - %s. Try with a valid Repository", repository_status)
            sys.exit(1)

        source_branch_existence_status = check_branch_existence(args.reponame, args.srcbranch)

        if source_branch_existence_status is False:
            logging.info("WARN: Source branch - %s not exists. Try with a valid source branch")
            sys.exit(1)

        new_branch_existence_status = check_branch_existence(args.reponame, args.newbranch)

        if source_branch_existence_status is True and new_branch_existence_status is False:
            logging.info("Source branch - %s exists and creating new branch in the repository named - %s",
                         args.srcbranch, args.newbranch)

            create_branch_from_existing_branch(args.reponame, args.srcbranch, args.newbranch)

            new_branch_existence_status = check_branch_existence(args.reponame, args.newbranch)

            # Check that the new branch was created.
            if new_branch_existence_status is False:
                logging.error("Failed to create the new branch")
                sys.exit(1)

        if source_branch_existence_status is True and new_branch_existence_status is True:
            default_branch_status = get_default_branch_status(args.reponame, args.srcbranch, args.newbranch)
            branch_protection_status = get_branch_protection_rules(args.reponame, args.newbranch)

            if default_branch_status == 'update' and args.updatedefault is True:
                update_default_branch(args.reponame, args.newbranch)

            if branch_protection_status == 'Not configured as expected':
                remove_branch_protection(args.reponame, args.newbranch)

            set_and_update_branch_protection(args.reponame, args.newbranch)

    except Exception as e:
        logging.info("Failed in Method - setup_new_branch() due to - " + str(e))
        print_exception_details(e)


def get_commit_details(repo_name, set_commits):
    """
    retrieves the details of the commit from the repository and log & save the commit details in a csv file
    :param set_commits: set of commit id
    :return: nothing
  """
    logging.info("RETRIEVING THE COMMIT DETAILS IN THE REPOSITORY - %s", repo_name)
    # HTTP url to access the get a specific branch endpoint of GitHub API
    url = _filetrek_url + repo_name + '/commits/'

    try:
        commit_details_list = [['Commit ID', 'URL', 'Author Name', 'Committer Name', 'Commit Message']]
        for commit in set_commits:
            response = requests.get(url=url + commit, headers=_headers)

            logging.debug('--------------------Details of commit - %s ---------------------', commit)
            logging.debug('URL - ' + response.json()['url'])
            logging.debug('Author - ' + response.json()['commit']['author']['name'])
            logging.debug('Committer - ' + response.json()['commit']['committer']['name'])
            logging.debug('Commit Message - ' + (response.json()['commit']['message']))
            commit_message = response.json()['commit']['message']
            commit_message = str(commit_message.encode('utf-8'))
            commit_details_list.append([commit, response.json()['url'],
                                        response.json()['commit']['author']['name'],
                                        response.json()['commit']['committer']['name'],
                                        commit_message
                                        ])

        logging.debug("Creating a CSV File for Commit Difference")
        csv_file_name = str(_work_dir) + '/' + repo_name + '_commit_info.csv'
        logging.info(
            'Creating a CSV File - ' + csv_file_name + 'for storing commit info for the repository -' + repo_name)
        csv_file = open(csv_file_name, 'w')
        logging.debug("Writing commit details in the CSV File - " + csv_file_name)
        writer = csv.writer(csv_file)
        writer.writerows(commit_details_list)
        csv_file.close()
    except Exception as e:
        logging.info(logging.info("Failed in get_commit_details() method due to - " + str(e)))
        print_exception_details(e)


def get_commit_list_from_git_log_file(f_name):
    """
    parse the log file and retrieve commit id's from it and save it in a list
    :param f_name: name of the log file
    :return: list of commit id retrieved from the log file
  """
    try:
        list_commits = []
        file = open(f_name, 'r')
        f_lines = file.readlines()

        for lines in f_lines:
            if lines.strip().__contains__('commit '):
                lines = lines.strip().replace('commit ', '')
                if lines.__len__() == 40 and not lines.__contains__(' '):
                    list_commits.append(lines)

        file.close()
        return list_commits
    except Exception as e:
        logging.info("Failed in clone_and_initialize_repo due to - " + str(e))
        print_exception_details(e)


def clone_repo(args):
    try:
        if _work_dir.exists() and _work_dir is not "/":
            shutil.rmtree(str(_work_dir))

        repo = Repo.clone_from(url='https://' + _authorization_token.replace('token ', '') +
                                   '@github.com/FileTrek/' + args.reponame + '.git', to_path=_work_dir,
                               branch=args.srcbranch)

        repo.create_head(args.newbranch)

        repo.git.checkout(args.newbranch)

    except Exception as e:
        logging.info("Failed in Method - clone_repo() due to - " + str(e))
        print_exception_details(e)


def branches_commit_difference(repo_name, src_branch, new_branch):
    """
    retrieve the list of commit id's in source and new branch using get_commit_list_from_git_log_file()
    and find the difference between the list of commits
    :return: a set of commit(s)
  """
    try:
        if _work_dir.exists() and _work_dir is not "/":
            shutil.rmtree(str(_work_dir))

        repo = Repo.clone_from(url='https://' + _authorization_token.replace('token ', '') +
                                   '@github.com/FileTrek/' + repo_name + '.git', to_path=_work_dir)

        repo.git.checkout(src_branch)
        f = open('source_branch_log', 'w')
        f.write(repo.git.log().encode('utf-8'))
        f.close()

        repo.git.checkout(new_branch)
        f = open('new_branch_log', 'w')
        f.write(repo.git.log().encode('utf-8'))
        f.close()

        list_src_branch_commits = get_commit_list_from_git_log_file('source_branch_log')
        list_new_branch_commits = get_commit_list_from_git_log_file('new_branch_log')

        logging.info('Number of commits in ' + src_branch + ' - ' + str(len(list_src_branch_commits)))
        logging.info('Number of commits in ' + new_branch + ' - ' + str(len(list_new_branch_commits)))

        logging.info('Calculating the Difference in number of commits between source and new branch')
        set_diff_commit = set(list_src_branch_commits) - set(list_new_branch_commits)
        logging.info('Number of different commits (src branch - new branch) - ' + str(len(set_diff_commit)))
        return set_diff_commit
    except Exception as e:
        logging.info("Failed in Method - branches_commit_difference() due to - " + str(e))
        print_exception_details(e)


def print_exception_details(exception):
    """
    print the details of expection - file name and line number
    :return: nothing
  """
    logging.error("==> Error - " + str(exception))
    exc_type, exc_obj, exc_tb = sys.exc_info()
    file_name = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print(exc_type, file_name, exc_tb.tb_lineno)


def display_branches(args):
    print("Display Branches")
    url = _filetrek_url + args.reponame + "/branches"
    response = requests.get(url=url, headers=_headers)
    print(json.dumps(response.json(), indent=4))


def create_pull_request(args):
    url = _filetrek_url + args.reponame + "/pulls"
    headers = {'Authorization': _authorization_token, 'Content-Type': 'application/json',
               'Accept': 'application/vnd.github.luke-cage-preview+json'}

    values = {
        "title": args.title,
        "body": args.message,
        "head": args.frombranch,
        "base": args.tobranch
    }

    print("VALUES")
    print(values)

    data = json.dumps(values)
    data = data.encode("utf-8")

    try:
        response = requests.post(url=url, headers=_headers, data=data)
        if response.status_code != 201:
            logging.info("==> Failed to create a pull request from branch %s to branch %s - failed due to error code"
                         " - %s and reason - %s", args.frombranch, args.tobranch, response.status_code, response.reason)
            sys.exit(1)

    except Exception as e:
        logging.info("==> HTTP Exception : " + str(e))
        print_exception_details(e)
        sys.exit(1)


logging.getLogger().setLevel(logging.INFO)  # Enable the logging settings
logging.getLogger("requests.packages.urllib3.connectionpool").setLevel(logging.ERROR)
logging.debug('Python Version - ' + sys.version)

# Arguments
# Common arguments
parser_common_a = argparse.ArgumentParser(add_help=False)
parser_common_a.add_argument('--key', required=True, type=str, help='The API Key')
parser_common_a.add_argument('--reponame', required=True, help='The repo name')

parser_common_b = argparse.ArgumentParser(add_help=False)
parser_common_b.add_argument('--srcbranch', required=True, help='The src branch')
parser_common_b.add_argument('--newbranch', required=True, help='The new branch')

parser = argparse.ArgumentParser(
    description='Performs various github tasks using the Github rest api or python git library')
subparsers = parser.add_subparsers(help='commands help')

# display_branches
parser_a = subparsers.add_parser('display_branches', parents=[parser_common_a],
                                 help='Displays a list of all the branches for a given repo')
parser_a.set_defaults(func=display_branches)

# setup_new_branch
parser_b = subparsers.add_parser('setup_new_branch', parents=[parser_common_a, parser_common_b],
                                 help='Setups up new branches in the given repo')
parser_b.set_defaults(func=setup_new_branch)
parser_b.add_argument('--updatedefault', default=False, action='store_true',
                      help='Set the default branch to the given new branch')

# verify_branch_setup
parser_c = subparsers.add_parser('verify_branch_setup', parents=[parser_common_a, parser_common_b],
                                 help='Verify that branch for a given repo is configured as expected.')
parser_c.set_defaults(func=verify_branch_setup)

# create_pull_request
parser_d = subparsers.add_parser('create_pull_request', parents=[parser_common_a], help='Create a pull request')
parser_d.set_defaults(func=create_pull_request)
parser_d.add_argument('--frombranch', required=True, help='The branch to pull the changes from')
parser_d.add_argument('--tobranch', required=True, help='The branch to push the changes into')
parser_d.add_argument('--title', required=True, help='The PR title')
parser_d.add_argument('--message', required=True, help='The PR message')

# clone_repo
parser_e = subparsers.add_parser('clone_repo', parents=[parser_common_a, parser_common_b], help='Create a pull request')
parser_e.set_defaults(func=clone_repo)

args = parser.parse_args()

# Initialize common static variables
_filetrek_url = "https://api.github.com/repos/shankarcs/"
_authorization_token = 'token ' + args.key
_headers = {'Authorization': _authorization_token}
_work_dir = Path(args.reponame)

try:
    args.func(args)
except TypeError as e:
    print_exception_details(e)
    parser.print_help()
    sys.exit(1)
except Exception as e:
    print_exception_details(e)
    sys.exit(1)
