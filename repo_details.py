"""
Main VIP program
"""
import re
from time import localtime, strptime, strftime
from git import Repo


def commit_contains_sub_paths(commit, sub_paths):
    """
    Determine if a commit contains changes to files that contain specific sub-paths
    :param commit: the commit
    :param sub_paths: a list of sub-paths. 'None' for changes to any files to be counted
    :return: True if the commit has changes to any of the specific sub-paths
    """
    if not sub_paths:
        return True

    if '*' in sub_paths:
        return True

    for file in commit.stats.files:
        for sub_path in sub_paths:
            if file.startswith(sub_path):
                return True

    return False


class RepoDetails:
    """
    The repo details class
    """
    def __init__(self, repo_path, datetime_format='%Y-%m-%d %H:%M:%S%z'):
        self.repo_path = repo_path
        self.datetime_format = datetime_format
        self._repo = Repo(repo_path)
        self._commit = self._repo.head.commit
        self._index = self._repo.index
        self._modification_count = None
        assert not self._repo.bare

    def branch_name(self):
        """
        The name of the currently checked out branch
        :return: the name of the branch as a string
        """
        return self._repo.active_branch

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

        return self._commit.hexsha[:num_chars]

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

    def has_modifications(self):
        """
        A bool if there are local modifications on the currently chekced out commit
        :return: True if there are modifications
        """
        return self.modification_count() > 0

    def version_output_function(self, match_pattern, tag, index):
        """
        Create the desired version number string
        :param match_pattern: the pattern that will match the tag
        :param tag: the first tag that matched the pattern
        :param index: the number of commits since the tag
        :return: a string representing a version number
        """
        major = '0'
        separator = '.'
        minor = '0'
        match = re.match(match_pattern, tag)
        if match:
            if match.group('major'):
                major = match.group('major')
            if match.group('separator'):
                separator = match.group('separator')
            if match.group('minor'):
                minor = match.group('minor')

        return '{0}{1}{2}{1}{3}{1}{4}'.format(major,
                                              separator,
                                              minor,
                                              index,
                                              self.modification_count())

    def version(self,
                tag_prefix='',
                tag_match_pattern=r'(?P<major>\d+)(?P<separator>[._-])(?P<minor>\d+)',
                sub_paths=None,
                output_function=version_output_function):
        """
        Search through commits to create the correct version number
        :param tag_prefix: what a matching tag should start with
        :param tag_match_pattern: the pattern after the tag prefix that should match
        :param sub_paths: a list of which sub-paths that will cause the version to increase if changes are made to
                          files that start with matching paths
        :param output_function: the function that will be called to actually create the version string
        :return: a version string
        """
        match_pattern = tag_prefix + tag_match_pattern
        tags = []
        for tag in self._repo.tags:
            if re.match(match_pattern, str(tag)):
                tags.append(tag)

        commits = list(self._repo.iter_commits())
        tag_name = ''
        index = 0
        for _, commit in enumerate(commits):
            for tag in tags:
                if tag.object.hexsha == commit.hexsha:
                    tag_name = tag.name
                    break

            if '' != tag_name:
                break

            if commit_contains_sub_paths(commit, sub_paths):
                index += 1

        return output_function(self, match_pattern, tag_name, index)

    def print_summary(self):
        """
        Prints a summary of the repository.
        :return: None
        """
        print(self.repo_path)
        print(self.branch_name())
        print(self.sha())
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
#    working_directory = os.path.dirname(os.path.realpath(__file__))
#    working_directory = 'C:\\Projects\\band_bringup'
    working_directory = 'C:\\Projects\\git\\test1'
    print(working_directory)
    repo_details = RepoDetails(working_directory)
    repo_details.print_summary()


if __name__ == "__main__":
    main()
