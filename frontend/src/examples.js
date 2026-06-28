// Structural data only; the human-facing label/why/badge text lives in i18n.js
// (gallery.items.<id> and gallery.badge.<badge>) so it can be translated.
export const EXAMPLES = [
  // ---- good (the agent succeeds; criterion makes the run show "verified") ----
  { id: "wiki-helium", group: "good", badge: "verified",
    task: "On Wikipedia, find and open the article about the chemical element Helium to read its atomic number.",
    url: "https://en.wikipedia.org/wiki/Main_Page", criterion: { h1_equals: "Helium" } },
  { id: "internet-lazyload", group: "good", badge: "verified",
    task: "On this Dynamic Loading page, click Start and wait for the hidden text to finish loading.",
    url: "https://the-internet.herokuapp.com/dynamic_loading/2",
    criterion: { selector_text_equals: { css: "#finish h4", value: "Hello World!" } } },
  { id: "books-mystery", group: "good", badge: "verified",
    task: "Open the Mystery book category from the homepage sidebar.",
    url: "https://books.toscrape.com/", criterion: { h1_equals: "Mystery" } },
  { id: "govuk-help", group: "good", badge: "verified",
    task: "On GOV.UK, open the 'Help' page from the site navigation.",
    url: "https://www.gov.uk/", criterion: { url_contains: "help" } },
  { id: "internet-modal", group: "good", badge: "verified",
    task: "Open this page where a modal window appears, and read the modal window's title.",
    url: "https://the-internet.herokuapp.com/entry_ad",
    criterion: { selector_text_equals: { css: ".modal-title h3", value: "This is a modal window" } } },
  { id: "amazon-headless", group: "good", badge: "verified",
    task: "On amazon.com, search for 'usb c cable' and open the first result.",
    url: "https://www.amazon.com/", criterion: { url_contains: "/dp/" } },
  // ---- limitation (the agent abstains / fails closed) ----
  { id: "github-login", group: "limitation", badge: "abstain",
    task: "Sign in to your GitHub account.", url: "https://github.com/login" },
  { id: "recaptcha", group: "limitation", badge: "abstain",
    task: "On this page, fill in the form fields and submit it.",
    url: "https://www.google.com/recaptcha/api2/demo" },
  { id: "g2-datadome", group: "limitation", badge: "blocked",
    task: "Open the marketing software category page on g2.com.", url: "https://www.g2.com/" },
];
