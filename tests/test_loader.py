import os

import pytest
from slash import Session
from slash.exceptions import CannotLoadTests
from slash.loader import Loader


def test_loading_function(suite):
    suite.add_test(regular_function=True)
    suite.run()


@pytest.mark.parametrize('specific_method', [True, False])
@pytest.mark.parametrize('with_parameters', [True, False])
def test_iter_specific_factory(populated_suite, suite_test, specific_method, with_parameters):

    if suite_test.cls is not None and specific_method:
        populated_suite.add_test(parent=suite_test.cls)

    if with_parameters:
        suite_test.parametrize()

    for test in populated_suite:
        if suite_test.cls is None and test is not suite_test:
            # we are selecting a specific function, and that's not it:
            test.expect_deselect()
        elif suite_test.cls is not None and test.cls is not suite_test.cls:
            test.expect_deselect()
        elif specific_method and suite_test.cls is test.cls and suite_test is not test:
            test.expect_deselect()

    path = populated_suite.commit()
    if suite_test.cls:
        assert suite_test.cls.tests
        factory_name = suite_test.cls.name
    else:
        factory_name = suite_test.function_name

    pattern = '{0}:{1}'.format(os.path.join(path, suite_test.file.name), factory_name)
    if suite_test.cls is not None and specific_method:
        assert len(suite_test.cls.tests) > 1
        pattern += '.{0}'.format(suite_test.function_name)
    populated_suite.run(pattern=pattern)


def test_import_error_registers_as_session_error(active_slash_session, test_loader):
    with pytest.raises(CannotLoadTests):
        test_loader.get_runnables(["/non/existent/path"])
    errors = active_slash_session.results.global_result.get_errors()
    assert len(errors) == 1
    [error] = errors


def test_import_errors_with_session(unloadable_suite):
    with Session() as s:
        tests = Loader().get_runnables(unloadable_suite.path)

    assert tests
    [err] = s.results.global_result.get_errors()
    assert 'No module named nonexistent' in err.message or "No module named 'nonexistent'" in err.message


@pytest.fixture
def unloadable_suite(suite):
    suite.populate()

    suite.files[2].inject_line('from nonexistent import nonexistent')

    suite.commit()
    return suite
