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
                 version_format='%M%s%m%s%p%s%mc',
                 use_directory_hash=False):
        """
        Initialize the RepoDetails object.
        :param repo_path: the path to the repository
        :param tag_prefix: what a matching tag should start with
        :param tag_match_pattern: the pattern after the tag prefix that should match
        :param sub_paths: a list of which sub-paths that will cause the version to increase if
                          changes are made to files that start with matching paths
        :param datetime_format: the default format for date/time stamps
        :param version_format: the default format for the version
        :param use_directory_hash: return the hash of the commit with the last change of the sub_paths
        """
        self.repo_path = repo_path
        self.tag_prefix = tag_prefix
        self.tag_match_pattern = tag_match_pattern
        self.datetime_format = datetime_format
        self.default_version_format = version_format
        self.sub_paths = []
        if sub_paths:
            for i in range(0, len(sub_paths)):
                sub_paths[i] = sub_paths[i].replace('\\', '/')
                sub_paths[i] = sub_paths[i].lstrip('/')
                self.sub_paths.append(sub_paths[i])

        self._repo = Repo(repo_path, odbt=GitCmdObjectDB)
        self._sub_path_commits = list(self._repo.iter_commits(paths=self.sub_paths))
        self._all_commits = list(self._repo.iter_commits())
        self._commit = self._repo.head.commit
        self._index = self._repo.index
        self._modification_count = None
        self._dir_modification_count = None
        self._use_directory_hash = use_directory_hash
        self._versions_dict = {}
        assert not self._repo.bare
        self._calculate_version_value()

    def _calculate_version_value(self):
        """
        Calculate version values: major, minor, patch
        :return: None
        """
        # Get all the tags that have the correct prefix and match the pattern.
        match_pattern = self.tag_prefix + self.tag_match_pattern
        tags = []
        for tag in self._repo.tags:
            if re.match(match_pattern, str(tag)):
                tags.append(tag)

        # Search through the commits from newest to oldest searching for one that contains a tag
        # that matches the pattern.
        commits = self._sub_path_commits
        tag_name = ''
        self._patch = 0
        for _, commit in enumerate(commits):
            for tag in tags:
                # if the commit sha matches one of the tag sha's then use this tag and break
                if tag.object.hexsha == commit.hexsha:
                    tag_name = tag.name
                    break

            if tag_name != '':
                break

            # increment the patch number
            self._patch += 1

        self._default_separator = '.'
        self._major = '0'
        self._minor = '0'
        self._patch = str(self._patch)

        # Use regex to pull the major and minor string from the tag, as well as the separator.
        match = re.match(match_pattern, tag_name)
        if match:
            if match.group('major'):
                self._major = match.group('major')
            if match.group('minor'):
                self._minor = match.group('minor')
            if match.group('separator'):
                self._default_separator = match.group('separator')

    def _apply_format(self, formatting, separator=None):
        """
        Apply formatting
        :param separator: the character that separates the different parts of the version
        :param formatting: the format string that has keywords that will be replaced
        :return: a string with replaced keywords
        """
        if not separator:
            separator = self._default_separator
        formatting = formatting.replace('%dmc', '{self.dir_mods()}')
        formatting = formatting.replace('%mc', '{self.mods()}')
        formatting = formatting.replace('%spr', '{self.semver_pre_release()}')
        formatting = formatting.replace('%sbm', '{self.semver_build_metadata()}')
        formatting = formatting.replace('%dsh', '{self.dir_sha()}')
        formatting = formatting.replace('%sh', '{self.sha()}')
        formatting = formatting.replace('%s', '{separator}')
        formatting = formatting.replace('%M', '{self._major}')
        formatting = formatting.replace('%m', '{self._minor}')
        formatting = formatting.replace('%p', '{self._patch}')
        formatting = formatting.replace('%hm', '{self.has_modifications()}')
        return eval(f'f"""{formatting}"""')

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
        return len(self._all_commits)

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
            return self.dir_sha(num_chars)

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

        commit = self._sub_path_commits[0]
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

    def mods(self):
        """
        The number of modifications on the currently checked out commit
        :return: the number of modifications as an int, or a string if a format is provided
        """
        if self._use_directory_hash:
            return self.dir_mods()

        if self._modification_count is None:
            self._modification_count = \
                len(self._all_commits[0].diff(None)) + len(self._all_commits[0].diff('HEAD'))

        return self._modification_count

    def dir_mods(self):
        """
        The number of modifications on the currently checked out commit
        :return: the number of modifications as an int, or a string if a format is provided
        """
        if self._dir_modification_count is None:
            self._dir_modification_count = \
                len(self._sub_path_commits[0].diff(None, self.sub_paths)) + \
                len(self._sub_path_commits[0].diff('HEAD', self.sub_paths))

        return self._dir_modification_count

    def has_mods(self, true_value=True, false_value=False):
        """
        A bool if there are local modifications on the currently checked out commit
        :return: True if there are modifications
        """
        if type(true_value) is str:
            true_value = self._apply_format(true_value)
        if type(false_value) is str:
            false_value = self._apply_format(false_value)
        return true_value if (self.mods() > 0) else false_value

    def has_dir_mods(self, true_value=True, false_value=False):
        """
        A bool if there are local modifications on the currently checked out commit
        :return: True if there are modifications
        """
        if type(true_value) is str:
            true_value = self._apply_format(true_value)
        if type(false_value) is str:
            false_value = self._apply_format(false_value)
        return true_value if (self.dir_mods() > 0) else false_value

    def version(self, separator=None, version_format=None):
        """
        The version in a <major>.<minor>.<patch>.<mods> format.
        :param separator: The separator to be used between parts of the version. If not supplied
                          the separator found in the tag will be used.
        :param version_format: an alternative format that can be used
        :return: A string of the version
        """
        if not version_format:
            version_format = self.default_version_format
        return self._apply_format(version_format, separator)

    def semver(self):
        """
        A simple semantic version based version that is <major>.<minor>.<patch>
        :return: A string of the semantic version
        """
        return self._apply_format('%M.%m.%p')

    def semver_extended(self):
        """
        An extended semantic version based version that is <major>.<minor>.<patch>-mods.<mods>+sha.<dir_sha7>
        :return: A string of the extended semantic version
        """
        return self._apply_format('%M.%m.%p%spr%sbm')

    def semver_pre_release(self):
        """
        The semver pre-release value based on the number of modifications
        :return: a string of the semver pre-release
        """
        return self.has_dir_mods('-mods.%mc', '')

    def semver_build_metadata(self):
        """
        The semver build metadata value based on the dir_sha
        :return: a string of the semver build metadata
        """
        return self._apply_format('+sha.%sh')

    def major(self):
        """
        The major value of the version
        :return: A string
        """
        return self._major

    def minor(self):
        """
        The minor value of the version
        :return: A string
        """
        return self._minor

    def patch(self):
        """
        The patch value of the version
        :return: A string
        """
        return self._patch

    def print_summary(self):
        """
        Prints a summary of the repository.
        :return: None
        """
        print(self.repo_path)
        print(self.branch_name())
        print(self.sha())
        print(self.dir_sha())
        print(str(self.mods()))
        print(str(self.dir_mods()))
        print(str(self.has_mods()))
        print(str(self.has_dir_mods()))
        print(self.commit_datetime())
        print(self.current_datetime())
        print(self.version())
        print(self.semver())
        print(self.semver_extended())


def main():
    """
    Run this main function if this script is called directly.
    :return: None
    """
    working_directory = os.path.dirname(os.path.realpath(__file__))
    print(working_directory)
    repo_details = RepoDetails(working_directory, sub_paths=['\\README.md'], use_directory_hash=True)
    repo_details.print_summary()


if __name__ == "__main__":
    main()
