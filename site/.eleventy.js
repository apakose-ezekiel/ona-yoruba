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

  // A-Z word list: Yoruba alphabet order (A B D E Ẹ F G GB H I J K L M N O Ọ P R S Ṣ T U W Y)
  const YO = ["a","b","d","e","ẹ","f","g","gb","h","i","j","k","l","m","n","o","ọ","p","r","s","ṣ","t","u","w","y"];
  const yoBase = (s) => (s || "").normalize("NFD").replace(/[\u0300\u0301\u0304]/g, "").normalize("NFC").toLowerCase();
  const yoKey = (s) => {
    s = yoBase(s).replace(/^[^a-zẹọṣ]+/, "");
    const out = [];
    for (let i = 0; i < s.length; i++) {
      const two = s.slice(i, i + 2);
      if (two === "gb") { out.push(YO.indexOf("gb")); i++; continue; }
      const k = YO.indexOf(s[i]);
      out.push(k === -1 ? 99 : k);
    }
    return out;
  };
  const yoCmp = (a, b) => {
    const x = yoKey(a), y = yoKey(b);
    for (let i = 0; i < Math.max(x.length, y.length); i++) {
      if ((x[i] ?? -1) !== (y[i] ?? -1)) return (x[i] ?? -1) - (y[i] ?? -1);
    }
    return 0;
  };
  eleventyConfig.addFilter("azGroups", (arr) => {
    const kinds = ["vocabulary", "deity", "royal_title", "odu"];
    const seen = new Set();
    const words = (arr || []).filter((e) => {
      if (!kinds.includes(e.type) || !e.yoruba) return false;
      const k = e.yoruba + "|" + (e.english || "");
      if (seen.has(k)) return false; // same word with the same meaning listed once
      seen.add(k);
      return true;
    });
    words.sort((a, b) => yoCmp(a.yoruba, b.yoruba));
    const groups = [];
    for (const e of words) {
      const k = yoKey(e.yoruba)[0];
      if (k === undefined || k === 99) continue;
      const letter = YO[k];
      let g = groups[groups.length - 1];
      if (!g || g.key !== letter) { g = { key: letter, label: letter.toUpperCase(), items: [] }; groups.push(g); }
      g.items.push(e);
    }
    return groups;
  });
  eleventyConfig.addFilter("dateFmt", (d) =>
    new Date(d).toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" })
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
