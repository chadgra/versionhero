"""
Main versionhero program.
"""
import argparse
import os
import re
import shutil
from time import time
from repo_details import RepoDetails


KEY_CHARACTERS = r'[!@#$%^&*]'


class VersionHero:
    """
    Main class the implements the file processing logic.
    """
    def __init__(self):
        self.args = ProgramArgs()

    def fetch_template_text(self):
        """
        Get the template text that will be keyword replaced
        :return: a string with the template text
        """
        if self.args.rename():
            return self.args.input_file()
        else:
            file = open(self.args.input_file(), 'r')
            file_text = file.read()
            file.close()
            return file_text

    def save_template_text(self, text):
        """
        Save the keyword replaced text to the correct location
        :param text: the keyword replaced text
        :return: None
        """
        if self.args.rename():
            shutil.copyfile(self.args.input_file(), text)
        else:
            if os.path.exists(self.args.backup_file()):
                os.remove(self.args.backup_file())

            if os.path.exists(self.args.output_file()):
                os.rename(self.args.output_file(), self.args.backup_file())

            file = open(self.args.output_file(), 'w')
            file.write(text)
            file.close()

    def execute(self):
        """
        Execute the VersionHero keyword replacement process
        :return: None
        """
        repo = RepoDetails(self.args.repo_dir(),
                           tag_prefix=self.args.tag_prefix(),
                           sub_paths=self.args.project_dirs(),
                           use_directory_hash=self.args.dir_hash())
        repo.print_summary()

        text = self.fetch_template_text()
        replacer = KeywordReplacer(text, repo)
        new_text = replacer.execute()
        self.save_template_text(new_text)


class ProgramArgs:
    """
    Setup the args and validate them.
    """
    def __init__(self):
        # Setup command-line args that we accept.
        parser = argparse.ArgumentParser(description='Parse an input file, replacing tags with ' +
                                         'information about the git repository.')

        parser.add_argument('template',
                            help='The template file.')
        parser.add_argument('--repo_dir', '-r', '-s', '--repo',
                            help='The repository - defaults to the current repository',
                            default='')
        parser.add_argument('--project_dir', '-p', '--project',
                            action='append',
                            help='Directory of a project in a git repository.  ' +
                            'Multiple directories can be included; put "-p" before each one.')
        parser.add_argument('--tag_prefix', '-tp',
                            help='The prefix of matching tags',
                            default='')
        parser.add_argument('--rename', '-rn',
                            action='store_true')
        parser.add_argument('--dir_hash', '-dh',
                            help='If specified, gets the hash for just the project directories',
                            action='store_true')

        self.args = parser.parse_args()
        self._input_file = None
        self._repo_dir = None
        self._project_dirs = None

    def input_file(self):
        """
        Get the input file path
        :return: the path of the input file as an absolute path
        """
        if self._input_file:
            return self._input_file

        input_file = self.args.template
        if not os.path.isabs(input_file):
            input_file = os.path.abspath(os.path.join(os.getcwd(), input_file))

        # If this file is to be renamed don't add '.git' to the end.
        if not self.rename():
            input_file = input_file if input_file.endswith('.git') else input_file + '.git'

        self._input_file = input_file
        return self._input_file

    def output_file(self):
        """
        Get the output file path
        :return: the path of the output file as an absolute path
        """
        return self._input_file[:-len('.git')]

    def backup_file(self):
        """
        Get the backup file path
        :return: the path of the backup file as an absolute path
        """
        return self.output_file() + '.bak'

    def repo_dir(self):
        """
        Get the repository directory
        :return: the repository directory as an absolute path
        """
        if self._repo_dir:
            return self._repo_dir

        # Initialize the repo_dir if it was empty or a relative path.
        repo_dir = self.args.repo_dir
        if not repo_dir or not os.path.isabs(repo_dir):
            repo_dir = os.path.abspath(os.path.join(os.getcwd(), repo_dir))

        # Find the root directory of the repository by looking for a '.git' folder.
        while not os.path.isdir(os.path.join(repo_dir, '.git')):
            repo_dir = os.path.abspath(os.path.join(repo_dir, '..'))

        self._repo_dir = repo_dir
        return self._repo_dir

    def project_dirs(self):
        """
        Get the project directory.
        :return: the project directory as a partial path.
        """
        if self._project_dirs:
            return self._project_dirs

        # Initialize the project_dir, which could be a sub-directory of the repository.
        project_dirs = []
        if self.args.project_dir:
            for project_dir in self.args.project_dir:
                if not os.path.isabs(project_dir):
                    project_dir = os.path.abspath(os.path.join(os.getcwd(), project_dir))
                project_dir = project_dir.replace(self.repo_dir(), '')
                if len(project_dir) == 0:
                    project_dir = '.'
                project_dirs.append(project_dir)
        self._project_dirs = project_dirs
        return self._project_dirs

    def tag_prefix(self):
        """
        Get the tag_prefix
        :return: the tag prefix as a string
        """
        return self.args.tag_prefix

    def rename(self):
        """
        Get the rename bool
        :return: True if the file name should be keyword exchanged, False if the files contents
                 should be keyword exchanged
        """
        return self.args.rename

    def dir_hash(self):
        """
        Get the dir_hash bool
        :return: True the sha/hash should be based on the project dirs, or if false, on the most recent commit
        """
        return self.args.dir_hash

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
        self.simple_replacement('GITMODCOUNT', self.repo_details.mods)
        self.simple_replacement('GITDIRMODCOUNT', self.repo_details.dir_mods)
        self.simple_replacement('GITCOMMITNUMBER', self.repo_details.commit_number)
        self.simple_replacement('GITCOMMITDATE', self.repo_details.commit_datetime,
                                r'(?P<datetime_format>.*)')
        self.simple_replacement('GITBUILDDATE', self.repo_details.current_datetime,
                                r'(?P<datetime_format>.*)')
        self.simple_replacement('GITHASH', self.repo_details.sha, r'(?P<num_chars>.*?)')
        self.simple_replacement('GITDIRHASH', self.repo_details.dir_sha, r'(?P<num_chars>.*?)')
        self.simple_replacement('GITMODS', self.repo_details.has_mods,
                                r'\?(?P<true_value>.*?):(?P<false_value>.*?)')
        self.simple_replacement('GITDIRMODS', self.repo_details.has_dir_mods,
                                r'\?(?P<true_value>.*?):(?P<false_value>.*?)')
        self.simple_replacement('GITVERSION', self.repo_details.version, r'(?P<separator>.*?)')
        self.simple_replacement('GITSEMVER', self.repo_details.semver)
        self.simple_replacement('GITSEMVEREX', self.repo_details.semver_extended)
        self.simple_replacement('GITMAJOR', self.repo_details.major)
        self.simple_replacement('GITMINOR', self.repo_details.minor)
        self.simple_replacement('GITPATCH', self.repo_details.patch)
        return self.text


def main():
    """
    Run this main function if this script is called directly.
    :return: None
    """
    start = time()
    version_hero = VersionHero()
    version_hero.execute()
    stop = time()
    print("{0:.2f} seconds to complete".format(stop - start))


if __name__ == "__main__":
    main()
