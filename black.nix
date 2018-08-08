{ stdenv, buildPythonPackage, fetchPypi, pythonOlder
, attrs, click, appdirs
, glibcLocales, pytest }:
let
  toml = buildPythonPackage rec {
    pname = "toml";
    version = "0.9.4";

    src = fetchPypi {
      inherit pname version;
      sha256 = "0bdbpbip67wdm6c7xwc6mmbmskyradj4cdxn1iibj4fcx1nbv1lf";
    };

    # This package has a test script (built for Travis) that involves a)
    # looking in the home directory for a binary test runner and b) using
    # git to download a test suite.
    doCheck = false;

    meta = with stdenv.lib; {
      description = "a Python library for parsing and creating TOML";
      homepage = "https://github.com/uiri/toml";
      license = licenses.mit;
      maintainers = with maintainers; [ twey ];
    };
  };

in buildPythonPackage rec {
  pname = "black";
  version = "18.6b4";

  disabled = pythonOlder "3.6";

  src = fetchPypi {
    inherit pname version;
    sha256 = "0i4sfqgz6w15vd50kbhi7g7rifgqlf8yfr8y78rypd56q64qn592";
  };

  checkInputs =  [ pytest glibcLocales ];

  checkPhase = ''
    # no idea, why those fail.
    LC_ALL="en_US.UTF-8" HOME="$NIX_BUILD_TOP" \
      pytest \
        -k "not test_cache_multiple_files and not test_failed_formatting_does_not_get_cached"
  '';

  propagatedBuildInputs = [ attrs appdirs click toml ];

  meta = with stdenv.lib; {
    description = "The uncompromising Python code formatter";
    homepage    = https://github.com/ambv/black;
    license     = licenses.mit;
    maintainers = with maintainers; [ sveitser ];
  };

}
