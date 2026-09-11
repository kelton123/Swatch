# LinkedIn post draft — Swatch

## The post

Every project I work on lives across three or four different pieces of software — Illustrator for boards, Revit for materials, Unreal for real-time visualisation. Every one of them wants colour in a different format.

So the hex code gets typed once, mistyped once, and by the third handoff nobody's sure which shade of "warm neutral" is actually correct anymore.

I got tired of it, so I built Swatch — a small desktop app (Python, Tkinter) for managing colour palettes across concurrent projects:

→ One dropdown switches every swatch between hex, RGB, CMYK and HSL — instantly, across the whole project
→ An eyedropper samples real pixels off the screen, correcting for display colour profile so what you pick is what you get
→ Each project tab autosaves independently and flags unsaved changes, the way a proper design tool should

It's a small tool, but it's the same instinct I bring to architecture: notice where a workflow is quietly wasting people's time, then go build the thing that fixes it.

Code's on GitHub (link in comments) — full case study on my site.

## Shorter hook variant (if you want something punchier for the opening line)

I kept mistyping hex codes moving between Illustrator, Revit and Unreal — so I built a tool to stop doing that.

---

# Media plan

LinkedIn ranks native video and image carousels above link posts, and it visibly suppresses reach on posts with an outbound link in the body — so keep the post itself link-free and put your GitHub/portfolio link in the **first comment** instead, posted immediately after you publish.

**Attachment order** (first item is what people see before they click "see more," so it has to work alone):

1. **Cover: 15–20s screen recording** — tab switch → colour format dropdown → eyedropper click → copied hex code. This one attachment will outperform every screenshot combined; software case studies live or die on showing motion.
2. **Screenshot — colour format dropdown open**, showing the format list (hex/rgb/cmyk/hsl). This is your single strongest "computational thinking" image.
3. **Screenshot — eyedropper mid-use.** Reads as the most technically impressive feature at a glance.
4. **Screenshot — tint/zoom controls.** Shows range beyond the obvious features.
5. **Screenshot — sketch next to the shipped main window**, side by side if you can composite it. This is the one most likely to make an architecture-trained reviewer trust the rest — it's the same "here's my process" language your thesis page already uses.

Five items is the right count — enough for a carousel to feel substantial without diluting the video's plays.

**Timing:** post the video-led version first. A week or two later, once it's had its run, publish a longer-form written article version linking to the full portfolio case study page — that gets you a second, separate wave of reach instead of splitting one post's attention.
