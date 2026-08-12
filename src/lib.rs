use pyo3::prelude::*;
use regex::Regex;
use std::sync::OnceLock;

const GROUP_NAMES: [&str; 14] = [
    "year",
    "monthdash",
    "month",
    "daydash",
    "day",
    "separator",
    "hour",
    "minute",
    "second",
    "second_fraction",
    "timezone",
    "tz_sign",
    "tz_hour",
    "tz_minute",
];

fn iso8601_regex() -> &'static Regex {
    static REGEX: OnceLock<Regex> = OnceLock::new();
    REGEX.get_or_init(|| {
        Regex::new(
            r"(?x)\A
            (?P<year>[0-9]{4})
            (
              (
                (-(?P<monthdash>[0-9]{1,2}))
                |
                (?P<month>[0-9]{2})
              )
              (
                (
                  (-(?P<daydash>[0-9]{1,2}))
                  |
                  (?P<day>[0-9]{2})
                )
                (
                  (
                    (?P<separator>[\x20T])
                    (?P<hour>[0-9]{2})
                    (:{0,1}(?P<minute>[0-9]{2})){0,1}
                    (
                      :{0,1}(?P<second>[0-9]{1,2})
                      ([.,](?P<second_fraction>[0-9]+)){0,1}
                    ){0,1}
                    (?P<timezone>
                      Z
                      |
                      (
                        (?P<tz_sign>[-+])
                        (?P<tz_hour>[0-9]{2})
                        :{0,1}
                        (?P<tz_minute>[0-9]{2}){0,1}
                      )
                    ){0,1}
                  ){0,1}
                )
              ){0,1}
            ){0,1}
            \z",
        )
        .expect("the frozen ISO 8601 parser regex must compile")
    })
}

fn matching_captures(datestring: &str) -> Option<regex::Captures<'_>> {
    // Python's `$` accepts a position immediately before one final LF.
    let subject = datestring.strip_suffix('\n').unwrap_or(datestring);
    let captures = iso8601_regex().captures(subject)?;

    // The upstream negative look-ahead rejects compact YYYYMM while allowing
    // dashed YYYY-MM. Rust's regex crate deliberately has no look-around.
    if captures.name("month").is_some()
        && captures.name("day").is_none()
        && captures.name("daydash").is_none()
    {
        return None;
    }

    Some(captures)
}

pub fn is_iso8601(datestring: &str) -> bool {
    matching_captures(datestring).is_some()
}

pub fn parse_components(datestring: &str) -> Option<Vec<(&'static str, String)>> {
    let captures = matching_captures(datestring)?;

    Some(
        GROUP_NAMES
            .iter()
            .filter_map(|name| {
                captures
                    .name(name)
                    .map(|value| (*name, value.as_str().to_owned()))
            })
            .collect(),
    )
}

#[pyfunction]
fn _parse_components(datestring: &str) -> Option<Vec<(&'static str, String)>> {
    parse_components(datestring)
}

#[pyfunction]
fn _is_iso8601(datestring: &str) -> bool {
    is_iso8601(datestring)
}

#[pymodule]
fn _native(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_function(wrap_pyfunction!(_parse_components, module)?)?;
    module.add_function(wrap_pyfunction!(_is_iso8601, module)?)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::{is_iso8601, parse_components};
    use std::collections::HashMap;

    fn groups(value: &str) -> Option<HashMap<&'static str, String>> {
        parse_components(value).map(|items| items.into_iter().collect())
    }

    #[test]
    fn parses_frozen_representative_forms() {
        for value in [
            "2014",
            "2014-02",
            "19950204",
            "2013-10-15T18Z",
            "2013-10-15T1130-0700",
            "2006-10-20T15:34:56.123+02:30",
            "1997-08-29T06:14:00,000123Z",
        ] {
            assert!(groups(value).is_some(), "{value}");
        }
    }

    #[test]
    fn rejects_frozen_invalid_forms() {
        for value in ["", "23", "201402", "2013-", "wibble", "2013-10-"] {
            assert!(groups(value).is_none(), "{value}");
        }
    }

    #[test]
    fn returns_named_components() {
        let parsed = groups("2006-10-20T15:34:56.123+02:30").unwrap();
        assert_eq!(parsed["year"], "2006");
        assert_eq!(parsed["monthdash"], "10");
        assert_eq!(parsed["second_fraction"], "123");
        assert_eq!(parsed["tz_sign"], "+");
        assert_eq!(parsed["tz_minute"], "30");
    }

    #[test]
    fn mirrors_python_final_lf_anchor() {
        assert!(groups("2006-10-20T15:34:56Z\n").is_some());
        assert!(groups("2006-10-20T15:34:56Z\n\n").is_none());
        assert!(is_iso8601("2006-10-20T15:34:56Z"));
        assert!(!is_iso8601("201402"));
    }
}
