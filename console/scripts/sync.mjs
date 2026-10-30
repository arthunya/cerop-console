// Copies the shared design tokens and the site data files into the console before dev/build,
// so the console reads exactly the JSON the site reads (built by site/build_data.py).
import { cpSync, mkdirSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, "..");
const site = join(root, "..", "site", "assets");
if (!existsSync(join(site, "data", "metrics.json"))) {
  throw new Error("site/assets/data is empty: run `python site/build_data.py` first");
}
mkdirSync(join(root, "public", "data"), { recursive: true });
cpSync(join(site, "data"), join(root, "public", "data"), { recursive: true });
cpSync(join(site, "css", "tokens.css"), join(root, "src", "tokens.css"));
cpSync(join(site, "img", "favicon.svg"), join(root, "public", "favicon.svg"));
console.log("synced tokens and data from site/assets");
