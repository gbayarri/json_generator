#!/usr/bin/env python3
"""Based on the https://www.conventionalcommits.org/en/v1.0.0/ convention
meaningful commit messages:

```
git commit -m "type(scope): subject Short description everything in the same line. \n\n Body long description:\n Avoid two consecutive line breaks. \n\n issue: https://github.com/bioexcel/biobb_XXX/issues/123"
```

Notes:
* subject and body are separated by a blank line.
* body and issue are separated by a blank line.
* scope: Anything the class, module name or general topic.
* type:
    * **build**: Changes that affect the build system or external dependencies.
    * **ci**: Changes to our CI configuration files and scripts.
    * **docs**: Documentation only changes.
    * **feat**: A new feature.
    * **fix**: A bug fix.
    * **perf**: A code change that improves performance.
    * **refactor**: A code change that neither fixes a bug nor adds a feature.
    * **style**: Changes that do not affect the meaning of the code (white-space, formatting, etc).
    * **test**: Adding missing tests or correcting existing tests.

Git tag for new version example:
```
git tag -a $version -m "version_number \n\n Change log file overview"
```
"""

import argparse
import json
from pathlib import Path
import re
import subprocess


def get_git_log(repo_dir):
    git_log_format = '\'{%n  "commit": "%H",%n  "abbreviated_commit": "%h",%n  "tree": "%T",%n  "abbreviated_tree": "%t",%n  "parent": "%P",%n  "abbreviated_parent": "%p",%n  "refs": "%D",%n  "encoding": "%e",%n  "subject": "%s",%n  "sanitized_subject_line": "%f",%n  "body": "%b",%n  "commit_notes": "%N",%n  "verification_flag": "%G?",%n  "signer": "%GS",%n  "signer_key": "%GK",%n  "author": {%n    "name": "%aN",%n    "email": "%aE",%n    "date": "%aD"%n  },%n  "commiter": {%n    "name": "%cN",%n    "email": "%cE",%n    "date": "%cD"%n  }%n},\''
    raw_json_log = subprocess.getoutput(f'cd {repo_dir} && git log --pretty=format:{git_log_format}')
    return json.loads(raw_json_log)


def get_tag_list(git_log, min_version):
    tag_list = []
    commit_pattern = re.compile(r"^((?P<type>build|ci|docs|feat|fix|perf|refactor|style|test)\((?P<scope>\w+)\):)(?P<message>.+)")
    issue_pattern = re.compile(r"issue: (?P<issue_url>http.+/issues/)(?P<issue_number>\d+)")
    tag_pattern = re.compile(r"tag: (?P<version>.*),*")
    for commit in git_log:
        # Tag Version
        commit_ref = commit.get('refs')
        if commit_ref:
            tag_dict = {'refs': tag_pattern.match(commit_ref).groupdict().get("version", '').replace("v", "").strip()}
            # Start Changelog in version 3
            try:
                version_num = int(tag_dict['refs'].replace(".", ""))
            except ValueError:
                return tag_list

            if version_num < min_version:
                return tag_list
            tag_dict['overview'] = commit.get('body').strip()
            tag_dict['feat'] = []
            tag_dict['fix'] = []
            tag_dict['other'] = []
            tag_list.append(tag_dict)
            continue

        # Commit
        if tag_list:
            commit_dict = {}
            commit_subject = commit_pattern.match(commit.get("subject", ""))
            if commit_subject:
                commit_dict = {k: v.strip() for k, v in commit_subject.groupdict().items()}

            commit_issue = issue_pattern.match(commit.get('body').split('\n\n')[-1])
            if commit_issue:
                commit_dict.update({k: v.strip() for k, v in commit_issue.groupdict().items()})

            commit_type = commit_dict.get('type')
            if commit_type:
                if commit_type.strip() in ['fix', 'feat']:
                    tag_dict[commit_type.strip()].append(commit_dict)
                else:
                    tag_dict['other'].append(commit_dict)

    return tag_list


def get_md_str_changelog(tag_list, repo_title, github_url):
    md_str = ""

    md_str += f"# {repo_title} changelog \n"
    md_str += f"\n"

    for tag in tag_list:
        md_str += f"## What's new in version [{tag['refs']}]({github_url}/releases/tag/{tag['refs']})"
        md_str += f"{tag['overview']}"
        md_str += f"\n"

        if tag.get('feat'):
            md_str += f"### New features\n"
            for feature in tag['feat']:
                if feature.get('message'):
                    md_str += f"* {feature['message']}"
                    if feature.get('scope'):
                        md_str += f"({feature['scope']})"
                    if feature.get('issue_url') and feature.get('issue_number'):
                        md_str += f"[#{feature['issue_number']}]({feature['issue_url']}{feature['issue_number']})"
                    md_str += f"\n"
        if tag.get('fix'):
            md_str += f"### Bug fixes\n"
            for feature in tag['fix']:
                if feature.get('message'):
                    md_str += f"* {feature['message']}"
                    if feature.get('scope'):
                        md_str += f"({feature['scope']})"
                    if feature.get('issue_url') and feature.get('issue_number'):
                        md_str += f"[#{feature['issue_number']}]({feature['issue_url']}{feature['issue_number']})"
                    md_str += f"\n"
        if tag.get('other'):
            md_str += f"### Other changes\n"
            for feature in tag['other']:
                if feature.get('message'):
                    md_str += f"* {feature['message']}"
                    if feature.get('scope'):
                        md_str += f"({feature['scope']})"
                    if feature.get('issue_url') and feature.get('issue_number'):
                        md_str += f"[#{feature['issue_number']}]({feature['issue_url']}{feature['issue_number']})"
                    md_str += f"\n"
    return md_str


def main():
    repo_dir = str(Path.cwd())
    repo_name = repo_dir.split("/")[-1]
    repo_url = f"https://github.com/bioexcel/{repo_name}/"
    output_file = str(Path.cwd().joinpath(repo_name, 'docs', 'source', 'change_log.md'))
    parser = argparse.ArgumentParser(description="Creates changelog.md",
                                     formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=99999),
                                     epilog="Examples: \nchangelog_generator.py -i path/to/git_repo/ -t RepoTitle -o path/output/file/changelog.md -v 300")
    required_args = parser.add_argument_group('required arguments')
    required_args.add_argument('--repo_path', '-i', required=False, default=repo_dir, type=str,
                               help='git repository folder in path/to/git_repo/')
    required_args.add_argument('--repo_title', '-t', required=False, default=repo_name.capitalize(), type=str,
                               help='Title of the repository as it will appear in the title of the changelog')
    required_args.add_argument('--github_url', '-g', required=False, default=repo_name.capitalize(), type=str,
                               help='Github.com url of the repository as it will appear in the browser url bar')
    required_args.add_argument('--output', '-o', required=False, default=output_file, type=str,
                               help='path/to/the/change_log.md')
    required_args.add_argument('--min_version', '-v', required=False, default=300, type=int, help='Minimum version to start the changelog file')

    args = parser.parse_args()

    git_log = get_git_log(args.repo_path)
    tag_list = get_tag_list(git_log, args.min_version)
    md_str = get_md_str_changelog(tag_list, args.repo_title, args.github_url)

    if md_str:
        with open(args.output, 'w') as changelog_fh:
            changelog_fh.write(md_str)
    else:
        print('Error generating changelog file')



