import streamlit as st
import tinycss2

# Page settings
st.set_page_config(
    page_title="CSS Parser and Inspector",
    page_icon="🔎",
    layout="centered"
)

st.title("🔎 CSS Parser and Inspector")
st.write(
    "Upload a CSS file to extract selectors, properties, "
    "values, media queries, keyframes, and detect syntax issues."
)

uploaded_file = st.file_uploader("Upload your CSS file")

if uploaded_file is not None:

    if not uploaded_file.name.lower().endswith(".css"):
        st.error("Invalid file format! Please upload a CSS file.")

    else:
        try:
            css_text = uploaded_file.getvalue().decode("utf-8")

            parsed_rules = []
            issues = []
            standalone_at_rules_count = 0

            # Helper to parse declarations inside a rule or keyframe block
            def parse_declarations(content_tokens, selector, condition=""):
                declarations = tinycss2.parse_declaration_list(
                    content_tokens,
                    skip_whitespace=True,
                    skip_comments=True
                )

                properties = []
                seen_properties = set()

                for declaration in declarations:
                    if declaration.type == "error":
                        issues.append(
                            f"Selector/Block '{selector}': {declaration.message}"
                        )
                    elif declaration.type == "declaration":
                        name = declaration.name
                        value = tinycss2.serialize(declaration.value).strip()
                        property_key = name.lower()

                        if property_key in seen_properties:
                            issues.append(
                                f"Duplicate property '{name}' inside '{selector}'."
                            )
                        seen_properties.add(property_key)

                        properties.append({
                            "Property": name,
                            "Value": value,
                            "Important": "Yes" if declaration.important else "No"
                        })

                parsed_rules.append({
                    "selector": selector,
                    "condition": condition,
                    "properties": properties
                })

            # Recursive stylesheet parser handling complex at-rules
            def parse_stylesheet(css, condition=""):
                
                rules = tinycss2.parse_stylesheet(
                    css,
                    skip_whitespace=True,
                    skip_comments=True
                )

                for rule in rules:
                    if rule.type == "error":
                        issues.append(f"Stylesheet error: {rule.message}")

                    elif rule.type == "qualified-rule":
                        selector = tinycss2.serialize(rule.prelude).strip()
                        if rule.content:
                            parse_declarations(rule.content, selector, condition)

                    elif rule.type == "at-rule":
                        keyword = rule.lower_at_keyword

                        # Standalone at-rules (e.g. @import, @charset) without content block
                        if rule.content is None:
                            standalone_at_rules_count += 1

                        # Handle @media and @supports (conditional grouping rules)
                        elif keyword in ("media", "supports"):
                            at_prelude = tinycss2.serialize(rule.prelude).strip()
                            new_condition = f"@{keyword} {at_prelude}"

                            if condition:
                                new_condition = f"{condition} / {new_condition}"

                            nested_css = tinycss2.serialize(rule.content)
                            parse_stylesheet(nested_css, new_condition)

                        # Handle @keyframes animations
                        elif keyword == "keyframes":
                            anim_name = tinycss2.serialize(rule.prelude).strip()
                            kf_condition = f"@keyframes {anim_name}"
                            if condition:
                                kf_condition = f"{condition} / {kf_condition}"

                            kf_rules = tinycss2.parse_stylesheet(
                                rule.content,
                                skip_whitespace=True,
                                skip_comments=True
                            )
                            for kf_rule in kf_rules:
                                if kf_rule.type == "qualified-rule":
                                    kf_selector = tinycss2.serialize(kf_rule.prelude).strip()
                                    if kf_rule.content:
                                        parse_declarations(
                                            kf_rule.content, 
                                            kf_selector, 
                                            kf_condition
                                        )

            # Start parsing
            parse_stylesheet(css_text)

            st.success(f"Uploaded: {uploaded_file.name}")

            # --- Summary Section ---
            st.subheader("📊 Summary Metrics")
            total_blocks = len(parsed_rules)
            total_properties = sum(len(rule["properties"]) for rule in parsed_rules)
            total_issues = len(issues)

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Rules / Blocks", total_blocks)
            col2.metric("Total Properties", total_properties)
            col3.metric("Issues Detected", total_issues)

            st.divider()

            # --- Parsed Rules Section ---
            st.subheader("Parsed CSS Structure")

            if parsed_rules:
                for item in parsed_rules:
                    if item["condition"]:
                        st.caption(f"Context / Condition: {item['condition']}")

                    st.markdown(f"**Selector / Step:** `{item['selector']}`")

                    if item["properties"]:
                        st.dataframe(
                            item["properties"],
                            hide_index=True,
                            use_container_width=True
                        )
                    else:
                        st.info("No declarations found in this block.")
            else:
                st.info("No valid CSS rules were found.")

            # --- Issues Section ---
            st.subheader("Issues & Diagnostics")
            if issues:
                for issue in issues:
                    st.warning(issue)
            else:
                st.success("No parser errors or duplicate properties detected.")

        except UnicodeDecodeError:
            st.error("Unable to read this file as UTF-8 text.")
        except Exception as error:
            st.error(f"Unable to process the file: {error}")

# Required explanation
st.divider()
st.subheader("Explanation of the CSS Parser")

st.markdown("""
- Extracts selectors, property names, values, `!important` flags, nested media queries (`@media`), feature queries (`@supports`), and animation keyframe steps (`@keyframes`).
- Provides overview statistics including total rule blocks, total property declarations and parsing issues.
- Reports malformed declarations and duplicate properties per rule block.
- **Edge case considered:** Detects when the same property appears more than once within a selector.""")
