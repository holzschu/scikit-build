"""This module defines custom implementation of ``bdist_wheel`` setuptools
command."""

from wheel.bdist_wheel import bdist_wheel as _bdist_wheel
from wheel.wheelfile import WheelFile

from .. import __version__ as skbuild_version
from ..utils import distribution_hide_listing
from . import set_build_base_mixin


class bdist_wheel(set_build_base_mixin, _bdist_wheel):  # type: ignore[misc]
    """Custom implementation of ``bdist_wheel`` setuptools command."""

    def run(self, *args: object, **kwargs: object) -> None:
        """Handle --hide-listing option."""

        old_write_files = WheelFile.write_files

        def update_write_files(wheelfile_self: "bdist_wheel", base_dir: str) -> None:
            with distribution_hide_listing(self.distribution) as hide_listing:
                if hide_listing:
                    zip_filename = wheelfile_self.filename
                    print(f"creating '{zip_filename}' and adding '{base_dir}' to it", flush=True)
                old_write_files(wheelfile_self, base_dir)

        WheelFile.distribution = self.distribution
        WheelFile.write_files = update_write_files

        try:
            super().run(*args, **kwargs)
        finally:
            WheelFile.write_files = old_write_files
            del WheelFile.distribution

            def _make_wheelfile_inner(base_name, base_dir='.'):
                with distribution_hide_listing(self.distribution) as hide_listing:
                    if hide_listing:
                        zip_filename = base_name + ".whl"
                        print("creating '%s' and adding '%s' to it"
                              % (zip_filename, base_dir))
                    old_make_wheelfile_inner(base_name, base_dir)

            _wheel_archive.make_wheelfile_inner = _make_wheelfile_inner

            try:
                super(bdist_wheel, self).run(*args, **kwargs)
            finally:
                _wheel_archive.make_wheelfile_inner = old_make_wheelfile_inner

    def finalize_options(self, *args, **kwargs):
        """Ensure MacOSX wheels include the expected platform information."""
        # pylint:disable=attribute-defined-outside-init,access-member-before-definition
        import sys
        if sys.platform == 'darwin' and self.plat_name is None and self.distribution.has_ext_modules():
            # The default value is duplicated in setuptools_wrap
            # pylint:disable=access-member-before-definition
            import os
            if "PLATFORM" in os.environ:
                platform=os.environ["PLATFORM"]
            else:
                platform="macosx"
            if platform == "macosx":    
                self.plat_name = os.environ.get('_PYTHON_HOST_PLATFORM', 'macosx-10.6-x86_64')
        super(bdist_wheel, self).finalize_options(*args, **kwargs)

    def write_wheelfile(self, wheelfile_base: str, _: None = None) -> None:
        """Write ``skbuild <version>`` as a wheel generator.
        See `PEP-0427 <https://www.python.org/dev/peps/pep-0427/#file-contents>`_ for more details.
        """
        generator = f"skbuild {skbuild_version}"
        super().write_wheelfile(wheelfile_base, generator)
