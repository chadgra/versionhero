"""
Main versionhero program.
"""
import argparse
import os
import re
from repo_details import RepoDetails


KEY_CHARACTERS = r'[!@#$%^&*]'


class KeywordReplacer:
    """
    The keyword replacer class.
    """
    def __init__(self, text, repo_details):
        """
        Create a KeywordReplacer object
        :param text: the text that will have keywords replaced
        :param repo_details: a RepoDetails object
        """
        self.repo_details = repo_details
        self.text = text

    def simple_replacement(self, keyword, substitution_lambda, keyword_arg_pattern='',
                           additional_args=None):
        """
        Replace the supplied keyword with the result of the substitution_lambda in the text of this
        object.
        :param keyword: the keyword to replace (not including any KEY_CHARACTERS)
        :param substitution_lambda: the lambda function to call to get the replacement text
        :param keyword_arg_pattern: some keywords can have additional arguments this is the regular
                                    expression match pattern
        :param additional_args: if any extra arguments needs to be passed into the
                                substitution_lambda pass them in this dictionary
        :return: None
        """
        keyword = str.format(r'{0}{1}{2}{0}', KEY_CHARACTERS, keyword, keyword_arg_pattern)
        while True:
            match = re.search(keyword, self.text)
            if match is None:
                break

            if not additional_args:
                additional_args = {}
            substitution_args = {**match.groupdict(), **additional_args}
            substitution = str(substitution_lambda(**substitution_args))
            self.text = self.text.replace(match.group(), substitution)

    def execute(self):
        """
        Execute all of the keyword replacements in the supplied text
        :return: the new text string
        """
        self.simple_replacement('GITBRANCHNAME', self.repo_details.branch_name)
        self.simple_replacement('GITMODCOUNT', self.repo_details.modification_count)
        self.simple_replacement('GITCOMMITNUMBER', self.repo_details.commit_number)
        self.simple_replacement('GITCOMMITDATE', self.repo_details.commit_datetime,
                                r'(?P<datetime_format>.*)')
        self.simple_replacement('GITBUILDDATE', self.repo_details.current_datetime,
                                r'(?P<datetime_format>.*)')
        self.simple_replacement('GITHASH', self.repo_details.sha, r'(?P<num_chars>.*)')
        self.simple_replacement('GITMODS', self.repo_details.has_modifications,
                                r'\?(?P<true_value>.*):(?P<false_value>.*)')
        self.simple_replacement('GITVERSION', self.repo_details.version, r'(?P<separator>.*)')
        return self.text


def main():
    """
    Run this main function if this script is called directly.
    :return: None
    """
    # Setup command-line args that we accept.
    parser = argparse.ArgumentParser(description='Parse an input file, replacing tags with ' +
                                                 'information about the git repository.')

    parser.add_argument('--template', '-t', '-f',
                        help='The template file.',
                        required=True)
    parser.add_argument('--repo_dir', '-r', '-s', '--repo',
                        help='The repository - defaults to the current repository',
                        default='')
    parser.add_argument('--project_dir', '-p', '--project',
                        help='Directory of a project in a git repository.')
    parser.add_argument('--tag_prefix', '-tp',
                        help='The prefix of matching tags',
                        default='')

    args = parser.parse_args()

    # Initialize the input and output files.
    input_file = args.template
    if not os.path.isabs(input_file):
        input_file = os.path.abspath(os.path.join(os.getcwd(), input_file))
    input_file = input_file if input_file.endswith('.git') else input_file + '.git'
    output_file = input_file[:-len('.git')]
    backup_file = output_file + '.bak'

    # Initialize the repo_dir if it was empty or a relative path.
    repo_dir = args.repo_dir
    if not repo_dir or not os.path.isabs(repo_dir):
        repo_dir = os.path.abspath(os.path.join(os.getcwd(), repo_dir))

    # Find the root directory of the repository by looking for a '.git' folder.
    while not os.path.isdir(os.path.join(repo_dir, '.git')):
        repo_dir = os.path.abspath(os.path.join(repo_dir, '..'))

    # Initialize the project_dir, which could be a sub-directory of the repository.
    project_dir = args.project_dir
    if not project_dir:
        project_dir = repo_dir
    elif not os.path.isabs(project_dir):
        project_dir = os.path.abspath(project_dir)
    project_dir = project_dir.replace(repo_dir, '')

    repo = RepoDetails(repo_dir, tag_prefix=args.tag_prefix, sub_paths=project_dir)
    repo.print_summary()

    file = open(input_file, 'r')
    file_text = file.read()
    file.close()
    replacer = KeywordReplacer(file_text, repo)

    if os.path.exists(backup_file):
        os.remove(backup_file)

    if os.path.exists(output_file):
        os.rename(output_file, backup_file)

    file = open(output_file, 'w')
    file.write(replacer.execute())
    file.close()


if __name__ == "__main__":
    main()
