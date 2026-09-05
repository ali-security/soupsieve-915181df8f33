"""Test attribute selectors."""
import signal
import unittest
import soupsieve as sv
from .. import util


class TestAttribute(util.TestCase):
    """Test attribute selectors."""

    MARKUP = """
    <div id="div">
    <p id="0">Some text <span id="1"> in a paragraph</span>.</p>
    <a id="2" href="http://google.com">Link</a>
    <span id="3">Direct child</span>
    <pre id="pre">
    <span id="4">Child 1</span>
    <span id="5">Child 2</span>
    <span id="6">Child 3</span>
    </pre>
    </div>
    """

    def test_attribute_not_equal_no_quotes(self):
        """Test attribute with value that does not equal specified value (no quotes)."""

        # No quotes
        self.assert_selector(
            self.MARKUP,
            'body [id!=\\35]',
            ["div", "0", "1", "2", "3", "pre", "4", "6"],
            flags=util.HTML5
        )

    def test_attribute_not_equal_quotes(self):
        """Test attribute with value that does not equal specified value (quotes)."""

        # Quotes
        self.assert_selector(
            self.MARKUP,
            "body [id!='5']",
            ["div", "0", "1", "2", "3", "pre", "4", "6"],
            flags=util.HTML5
        )

    def test_attribute_not_equal_double_quotes(self):
        """Test attribute with value that does not equal specified value (double quotes)."""

        # Double quotes
        self.assert_selector(
            self.MARKUP,
            'body [id!="5"]',
            ["div", "0", "1", "2", "3", "pre", "4", "6"],
            flags=util.HTML5
        )

    @unittest.skipUnless(hasattr(signal, 'SIGALRM'), 'Requires SIGALRM which is unavailable on Windows')
    def test_bad_attribute_unclused(self):
        """Test bad attribute fails for syntax error, not timeout error."""

        def timeout_handler(signum, frame):
            """Abort the parse that is taking too long."""

            raise TimeoutError

        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(3)

        passed = False
        try:
            with self.assertRaises(sv.SelectorSyntaxError):
                sv.compile('[a="' + ('x' * 300))
            passed = True
        except TimeoutError:
            pass
        finally:
            signal.alarm(0)
        self.assertTrue(passed)

    @unittest.skipUnless(hasattr(signal, 'SIGALRM'), 'Requires SIGALRM which is unavailable on Windows')
    def test_bad_value_unclosed(self):
        """
        Test that every pattern built on the attribute value pattern fails fast.

        The value pattern is shared by attribute selectors and by `:-soup-contains()` and `:lang()`,
        so an unterminated value must raise a syntax error instead of backtracking catastrophically.
        """

        def timeout_handler(signum, frame):
            """Abort the parse that is taking too long."""

            raise TimeoutError

        payloads = (
            # Unterminated double quoted value.
            '[a="' + ('x' * 300),
            # Unterminated single quoted value.
            "[a='" + ('x' * 300),
            # Unterminated identifier value.
            '[a=' + ('x' * 300),
            # Same values, but for the pseudo classes that reuse the value pattern.
            ':-soup-contains("' + ('x' * 300),
            ':-soup-contains(' + ('x' * 300),
            ':lang("' + ('x' * 300),
            ':lang(' + ('x' * 300)
        )

        original = signal.signal(signal.SIGALRM, timeout_handler)
        try:
            for payload in payloads:
                passed = False
                signal.alarm(3)
                try:
                    with self.assertRaises(sv.SelectorSyntaxError):
                        sv.compile(payload)
                    passed = True
                except TimeoutError:
                    pass
                finally:
                    signal.alarm(0)
                self.assertTrue(passed, 'Selector {!r} did not fail fast'.format(payload))
        finally:
            signal.signal(signal.SIGALRM, original)
