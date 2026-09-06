module.exports = function (eleventyConfig) {
  eleventyConfig.addPassthroughCopy("src/assets");
  // Ported as-is from sources/kojoda-complete.html -- a complete, already
  // well-written standalone page. Excluded from templating (it's a full,
  // self-contained document with its own <html>/<style>) and passed through
  // as a raw file instead, so nothing in its embedded CSS/JS gets touched.
  eleventyConfig.ignores.add("src/pillars/philosophy-cosmology/kojoda.html");
  eleventyConfig.addPassthroughCopy({
    "src/pillars/philosophy-cosmology/kojoda.html": "pillars/philosophy-cosmology/kojoda/index.html",
  });

  eleventyConfig.addFilter("json", (value) => JSON.stringify(value));

  eleventyConfig.addFilter("badge", (verifyStatus) => {
    const map = {
      verified_multi_source: { label: "Verified (multi-source)", cls: "verified" },
      verified_single_source: { label: "Sourced", cls: "verified" },
      fieldwork_verified: { label: "Fieldwork verified", cls: "verified" },
      fieldwork_partial: { label: "Fieldwork (partial)", cls: "partial" },
      ai_generated_unverified: { label: "AI research — unverified", cls: "unverified" },
      web_sourced_pending_verification: { label: "Community-sourced — unverified", cls: "unverified" },
      disputed: { label: "Disputed sources", cls: "disputed" },
      unverified: { label: "Unverified", cls: "unverified" },
    };
    return map[verifyStatus] || { label: verifyStatus, cls: "unverified" };
  });

  eleventyConfig.addFilter("where", (arr, key, value) =>
    (arr || []).filter((item) => item[key] === value)
  );

  eleventyConfig.addFilter("limit", (arr, n) => (arr || []).slice(0, n));

  return {
    pathPrefix: "/ona-yoruba/",
    dir: {
      input: "src",
      output: "_site",
      includes: "_includes",
    },
  };
};
