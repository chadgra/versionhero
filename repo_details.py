"""
Main VIP program
"""
import re
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
    def __init__(self, repo_path):
        self.repo_path = repo_path
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

    def sha(self, num_chars=7):
        """
        The sha of the currently checked out commit
        :param num_chars: the number of characters to return
        :return: the sha as a string
        """
        return self._commit.hexsha[:num_chars]

    def datetime(self):
        """
        The datetime of the currently checked out commit
        :return: the date time as a string
        """
        return self._commit.authored_datetime

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
        match = re.match(match_pattern, tag.name)
        if match:
            return '{0}{1}{2}{1}{3}{1}{4}'.format(match.group('major'),
                                                  match.group('separator'),
                                                  match.group('minor'),
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
        index = 0
        for _, commit in enumerate(commits):
            for tag in tags:
                if tag.object.hexsha == commit.hexsha:
                    return output_function(self, match_pattern, tag, index)

            if commit_contains_sub_paths(commit, sub_paths):
                index += 1


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
    print(repo_details.branch_name())
    print(repo_details.sha())
    print(repo_details.sha(5))
    print(repo_details.sha(40))
    print(repo_details.datetime())
    print(str(repo_details.modification_count()))
    print(str(repo_details.has_modifications()))
    print(repo_details.version(tag_prefix='dir1_', sub_paths=['dir1']))


if __name__ == "__main__":
    main()