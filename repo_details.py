"""
Get information about a repository.
"""
import os
import re
from time import localtime, strptime, strftime
from git import Repo, GitCmdObjectDB


class RepoDetails:
    """
    The repo details class
    """
    def __init__(self,
                 repo_path,
                 tag_prefix='',
                 tag_match_pattern=r'(?P<major>\d+)(?P<separator>[._-])(?P<minor>\d+)',
                 sub_paths=None,
                 datetime_format='%Y-%m-%d %H:%M:%S%z',
                 use_directory_hash=False):
        """
        Initialize the RepoDetails object.
        :param repo_path: the path to the repository
        :param tag_prefix: what a matching tag should start with
        :param tag_match_pattern: the pattern after the tag prefix that should match
        :param sub_paths: a list of which sub-paths that will cause the version to increase if
                          changes are made to files that start with matching paths
        :param datetime_format: the default format for date/time stamps
        """
        self.repo_path = repo_path
        self.tag_prefix = tag_prefix
        self.tag_match_pattern = tag_match_pattern
        self.datetime_format = datetime_format
        self.sub_paths = []
        if sub_paths:
            for i in range(0, len(sub_paths)):
                sub_paths[i] = sub_paths[i].replace('\\', '/')
                sub_paths[i] = sub_paths[i].lstrip('/')
                self.sub_paths.append(sub_paths[i])

        self._repo = Repo(repo_path, odbt=GitCmdObjectDB)
        self._commit = self._repo.head.commit
        self._index = self._repo.index
        self._modification_count = None
        self._use_directory_hash = use_directory_hash
        assert not self._repo.bare

    def branch_name(self):
        """
        The name of the currently checked out branch
        :return: the name of the branch as a string
        """
        try:
            return self._repo.active_branch
        except TypeError:
            return "detached"

    def commit_number(self):
        """
        The number of commits in the history of the currently checked out branch
        :return: the number of commits
        """
        return len(list(self._repo.iter_commits()))

    def sha(self, num_chars=7):
        """
        The sha of the currently checked out commit
        :param num_chars: the number of characters to return
        :return: the sha as a string
        """
        try:
            num_chars = int(num_chars)
        except ValueError:
            num_chars = 7

        if self._use_directory_hash:
            return self.dir_sha

        return self._commit.hexsha[:num_chars]

    def dir_sha(self, num_chars=7):
        """
        The sha of the most recent commit with changes to a file in the sub_paths.
        :param num_chars: the number of characters to return
        :return: the sha as a string
        """
        try:
            num_chars = int(num_chars)
        except ValueError:
            num_chars = 7

        commit = list(self._repo.iter_commits(paths=self.sub_paths))[0]
        return commit.hexsha[:num_chars]

    def commit_datetime(self, datetime_format=None):
        """
        The datetime of the currently checked out commit
        :return: the date time as a string
        """
        if not datetime_format:
            datetime_format = self.datetime_format
        authored_datetime = ''.join(str(self._commit.authored_datetime).rsplit(':', 1))
        time_structure = strptime(authored_datetime, '%Y-%m-%d %H:%M:%S%z')
        return strftime(datetime_format, time_structure)

    def current_datetime(self, datetime_format=None):
        """
        The datetime right now
        :return: the date time as a string
        """
        if not datetime_format:
            datetime_format = self.datetime_format
        return strftime(datetime_format, localtime())

    def modification_count(self):
        """
        The number of modifications on the currently checked out commit
        :return: the number of modifications as an int
        """
        if self._modification_count is None:
            self._modification_count = \
                len(self._index.diff(None)) + len(self._index.diff('HEAD'))
        return self._modification_count

    def has_modifications(self, true_value=True, false_value=False):
        """
        A bool if there are local modifications on the currently checked out commit
        :return: True if there are modifications
        """
        return true_value if (self.modification_count() > 0) else false_value

    def version_output_function(self, separator, match_pattern, tag, index):
        """
        Create the desired version number string
        :param separator: the character that separates the different parts of the version
        :param match_pattern: the pattern that will match the tag
        :param tag: the first tag that matched the pattern
        :param index: the number of commits since the tag
        :return: a string representing a version number
        """
        major = '0'
        minor = '0'
        match = re.match(match_pattern, tag)
        if match:
            if match.group('major'):
                major = match.group('major')
            if match.group('minor'):
                minor = match.group('minor')
            if separator is None or separator is '':
                if match.group('separator'):
                    separator = match.group('separator')

        if separator is None or separator is '':
            separator = '.'

        return '{0}{1}{2}{1}{3}{1}{4}'.format(major,
                                              separator,
                                              minor,
                                              index,
                                              self.modification_count())

    def version(self,
                separator=None,
                output_function=version_output_function):
        """
        Search through commits to create the correct version number
        :param separator: the character that separates the different parts of the version
        :param output_function: the function that will be called to actually create the version
                                string
        :return: a version string
        """
        match_pattern = self.tag_prefix + self.tag_match_pattern
        tags = []
        for tag in self._repo.tags:
            if re.match(match_pattern, str(tag)):
                tags.append(tag)

        commits = list(self._repo.iter_commits(paths=self.sub_paths))
        tag_name = ''
        index = 0
        for _, commit in enumerate(commits):
            for tag in tags:
                if tag.object.hexsha == commit.hexsha:
                    tag_name = tag.name
                    break

            if tag_name != '':
                break

            index += 1

        return output_function(self, separator, match_pattern, tag_name, index)

    def print_summary(self):
        """
        Prints a summary of the repository.
        :return: None
        """
        print(self.repo_path)
        print(self.branch_name())
        print(self.sha())
        print(self.dir_sha())
        print(str(self.modification_count()))
        print(str(self.has_modifications()))
        print(self.commit_datetime())
        print(self.current_datetime())
        print(self.version())


def main():
    """
    Run this main function if this script is called directly.
    :return: None
    """
    working_directory = os.path.dirname(os.path.realpath(__file__))
    print(working_directory)
    repo_details = RepoDetails(working_directory, sub_paths=['\\README.md'])
    repo_details.print_summary()


if __name__ == "__main__":
    main()
