# The studio image (optional, Higgsfield)

This step only runs when the Higgsfield connector is on in the chat (its tools appear in the tool
list, for example an image generation tool). If it is not connected, skip the step and say one
line: "Higgsfield isn't connected, so I'll skip the studio photo and build the game." Never ask the
user for an API key and never try another paid service instead.

## Credit gate

Image generation spends the user's Higgsfield credits. Before calling any generation tool:

1. If a balance or credits tool exists, check it and tell the user what they have.
2. Show the exact prompt below, filled in from car.json.
3. Ask: **"This uses your Higgsfield credits. Generate the studio photo?"** Wait for a yes.

One image per yes. Do not batch, retry in a loop, or upscale without a new yes.

## The prompt

Fill the brackets from car.json. Leave out any clause the spec does not have.

```
Studio photograph of a [main colour] [body], rear three-quarter view from the left,
[two/one/three] [stripe colour] racing stripes running over the hood, roof and trunk,
[a big [spoiler colour] rear wing on two posts | a small ducktail lip spoiler], [N] exhaust tips,
rear licence plate reading "[PLATE]". Plain dark charcoal seamless background, soft studio
lighting, gentle floor reflection, the whole car in frame. No other text, no logos, no
watermark, no people.
```

Settings: a 16:9 or 4:3 image if the tool asks for an aspect ratio. Use the tool's default image
model unless the user names one.

## After it comes back

Show the image next to a one-line check against the sketch: stripes, spoiler, colour, plate.
If something is wrong (one stripe instead of two, no wing), offer one corrected generation with
the fix added to the prompt, behind the same credit question. The game build does not depend on
this image; the game draws the car from car.json.
