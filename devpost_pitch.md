# OrdSimilarity project

## Motto / goal

_Create a search engine for ordinals pictures determining their similarity._

[Initial pitch for the idea](https://www.loom.com/share/43b6254bdd784f6fb0404711780a5e0f)

[Final submission of the result](https://www.youtube.com/watch?v=kkXcYjOSU9g
)

## Inspiration

The inspiration behind building `OrdSimilarity` comes from the lack of a standardized approach to ensure the uniqueness of ordinals in the `Bitcoin` blockchain. As the number of ordinals being created and traded increases, it becomes challenging for creators and collectors to distinguish whether their ordinals are genuinely one-of-a-kind or if there are already similar or identical ones in existence. This issue can lead to disputes over ordinal ownership which can cause potential buyers to hesitate and question the value of the ordinal. This can lead to a lack of demand for the affected ordinal, ultimately resulting in a decline in its market price.

![the ordinal is mine](https://i.ibb.co/93PFZF2/mine.png)

Another source of inspiration was our interest in data science combined with `Bitcoin`. We wanted to understand the data ourselves and eventually found out that the insights would be valuable for others as well.

## What it does

Offers a frontend `UI` and public `API` to interact with a picture search-engine, looking for similar ordinals. Users can input either a custom file or ordinal ID and the service returns a list of most similar ordinals that already exist.

`OrdSimilarity` solves the challenge of ensuring ordinal uniqueness on the Bitcoin blockchain by using an algorithm that compares the user's proposed ordinal with all pre-existing ordinals on the blockchain. The algorithm analyzes the ordinal's content and computes its similarity score with other ordinals. Then, it provides a list of the most similar ordinals to the proposed one, with specifically flagging pixel-perfect copies. With its fast and reliable computation, `OrdSimilarity` allows users to quickly verify the uniqueness of their ordinals with minimal effort.

## How we built it

First thing was to develop a sensible way to create a data representation of the image, so that we can compare how similar it is with representations of other images. In the end, we went with `Average hash` and `Hamming distance` - details at [this link](https://www.hackerfactor.com/blog/index.php?/archives/432-Looks-Like-It.html). With this approach, we can represent the whole image by a list of (in our case 256) bits, which is a representation where we can quickly tell how similar two of them are (how many bits are the same). This bit representation can be very conveniently stored in a simple `JSON` file as a string of "0"s and "1"s, loaded and compared relatively quickly.

Next up, we gathered all the data we will be working with. In our case that is information about all the ordinals in existence - both their metadata (ord_id, time, content_type,…) and the actual inscribed byte content. We used our BTC full-node to get the authoritative data on all the already existing ordinals and filled our databases with these data. For getting updates on the latest inscribed ordinals, we are using `Hiro API` - contacting them regularly and fetching all the data we do not already have.

After we had all the ordinal data, we would apply our classification algorithm to the content of all image ordinals in existence - more than 500_000 of them at the moment. Some of the image formats like `image/svg+xml` were problematic to classify, so we did not include them (logic - try to classify it and when it fails, go on) - however, these are only a small part of the image space (according to https://btcstatts.com).

Having a `JSON` file with `ord_id: average_hash` string mapping, we could already create an MVP `python` script accepting the average*hash and finding N ord_ids with the most similar average_hashes. But as you can imagine, comparing 256-character strings half a million times does take a while in `python`. So we employed `Rust`, rewrote the logic in it and got a \_5-7 times speedup*. One nice thing about this is that we could actually create a shared `Rust` library in `C`-style compatible way and call it directly from `python` - so we could still have `python` API on the surface, which is easier to work with and users of the script do not care what happens inside.

Now the speed was already okay-ish, but not good enough. Profiling the code showed that the majority of the time in `Rust` is being spent by loading the `JSON` file (which has around `130 MB`). The obvious question was how to minimize the data loading time, which was even higher in the `python` case. Replacing the `JSON` file with some other data structure like `sqlite3` `DB` did not help, it turned out that when we need to really get all the data, `JSON` file is actually a very good way of storing data on disk.

But what about if we would store the data in memory, that should be quicker, right? At that time I was creating the API for the project (my first one in `FastAPI`, and it is really better than `Flask`), and realized something - all the requests have immediate access to all global variables, without having to load them from disk - _that is the place where we should put our `JSON` data_! It turned out that loading the file at server startup and having the data available immediately meant that we almost did not have to use `Rust` - the `python` performance was close enough. But `Rust` should be able to run an `HTTP` server as well, or not? A couple of `ChatGPT` queries later and we have a working `Rust` server that returns the result of 500_000 \* 256 string character comparisons in less than half a second after receiving the request.

It is a hackathon, isn’t it? Do we want the best speed? _Yes!_ Have we heard of indexing? _Yes!_ So let’s do it. My laptop was not very happy during those 20-something hours of running two `Rust` scripts on 80% `CPU`, collaboratively comparing half a million images between each other. (It was a little noisy, so it spent the night in the bathroom. I have a photo of it.) How many comparisons between "0"s and "1"s did it did? No idea, around 500_000 _ 500_000 _ 256.

Does it mean that if we compared all the images in the dataset between each other, saving 20 most similar pictures for each of them, did we win the game? _No, because the game never ends._ During the indexing new ordinals were minted, and that means the full indexing can never be finished (without very heavy real-time updates).

Were we sad? _Yes._ Did we cry? _No._ Instead, we have realized something - the index is still very useful, even if it is not complete. Suppose we have compared an image (call it `image-X`) to all of the images up to ID 1000 and we saved 20 most similar ones into the index. New images are created, and there are suddenly 1100 of them. Now, when asked for `image-X` similarities, we need to calculate the similarity only for the last 100 that are not in the index already. Then we merge the TOP20 in the index with TOP20 from the new comparisons. We can return TOP20 to the client and update the index as a bonus - now the index of `image-X` is up-to-date until ID 1100. During this revelation moment, a potential proverb occurred to me - _"when nobody is asking, we do not need to know the answer"_. It is enough to know how to calculate it relatively quickly.

Armed with a lightning-quick similarity `API`, we could deploy it (https://api.ordsimilarity.com/) and move our attention to the client side. The deployment on `HTTPS` was a little challenging, but Apache was collaborating in the end.

As the link above suggests, we bought a `.com` domain for the project, because we want to get more public visibility. Who would like to use `API` under http://1.2.3.4:8081?

For the frontend we chose a simple website, running at https://ordsimilarity.com. We do not use any `Javascript` framework and keep the functionality to a minimum. The valuable benefit of just vanilla `HTML+CSS+JS` is that we can literally redeploy the whole frontend in one second - just replacing 3 files on the server. We have also set up a dev instance, where we were testing the new stuff before deploying to production - https://dev.ordsimilarity.com.

The website hopefully does what it promises - offers a client to the search-engine `API`, allowing to upload a custom file or choose an ordinal ID and it gives you 20 most similar ordinals in existence.

The similarity is shown in percentages, e.g. a figure of `98,83 %` means that out of the 256-bit image representation, 253 bits are matching. When the match is `100 %`, that means the representations of the images are identical, but not necessarily the images themselves. To recognize and flag images that are really pixel-perfect duplicates, we can compare the `MD5` hashes of the image content bytes, which are being returned from `API`.

When users upload their own custom picture, we offer them a direct link to a minting service, where they could mint the ordinal. That could be a potential opportunity to partner with a minting service to support us.

We could not resist adding some nice-to-have features like keyboard shortcuts or an extra footer to tease the user to try it.

The `Feeling lucky` button was created so users have easier first-step interaction with the website - it saves them the time/energy to come up with some picture or `ord_id` to see the site’s behaviour. It is also very nice for developers who could visually test the approximate correctness of the similarity algorithm.

During one of the tests we came across one disturbing image, and immediately created an issue to delete all of these from `DB` (not sure how to identify them though). Until then you can safely browse only after 10pm or at your own risk!

Searches by `ord_id` will also modify the `URL` of the website to include the query for this `ord_id`, so users could send it to others and they would see the same results when entering the `URL`. It would be viable to support this even for custom picture searches - we need to read the custom picture content on server anyway, so we may as well store it on disk.

Having more time we would probably replace the calls to `alert()` with a custom error popup. Now we believe it is a punishment to the user - you gave me invalid input, you will be punished by an ugly default alert!.

Frontend has one additional dependency apart from our own `API` - and that is `Hiro API`, which helps us with showing the pictures on the frontend. Their [inscription content API](https://docs.hiro.so/ordinals#tag/Inscriptions/paths/~1ordinals~1v1~1inscriptions~1%7Bid%7D~1content/get) is a very good fit for this use-case, because it means we do not have to send the picture data in `API` response (which would be potentially huge), nor we have to host/provide the content on our own server.

We have verified the site on `Google`, were already added to the index (it can be found under "ordsimilarity" and rejecting the "Did you mean word similarity?" suggestion). According to `Google Analytics` we had 34 unique visitors during the first 40 hours of the website running. Our `API` logs tell us that we had 22 unique `IP` addresses using the `API`.

Have we tried it on mobile? _Yes!_ Does it look decent there? _I hope so!_

During the hackathon we were diligently opening and closing Github issues, doing the majority of changes through PRs. Check out the [outstanding issues](https://github.com/grdddj/similar-ordinals/issues).

## Business Prospects

Below are some potential revenue streams for `OrdSimilarity`:

1. **Monetizing our API:** Our comparison algorithm is unique, and the fastest possible. We can monetize this API by offering it to ordinal minting platforms to verify the uniqueness of their users' ordinals before they mint one. We could charge these platforms a fee for each use of the `API`, creating a potential revenue stream.

2. **Subscription based service for individual users:** `OrdSimilarity` could offer a subscription-based service to individual ordinal creators and collectors. Users would pay a monthly or yearly fee to access the platform's services. This could be an attractive option for users who frequently mint or collect ordinals and want to ensure their uniqueness.

3. **Advertising / Promotion**: We also offer promotional spaces to other entities in the ordinal space. For instance, we have a `Mint Here` button on the website which can promote a specific ordinal minting platform. In exchange for this promotion, these entities could offer a commission on any sales that result from the promotion.

## Challenges we ran into

At first, we had no idea how to even compare the similarity between two images. We needed a classification algorithm that would be both quick to run and compare (even for big datasets) and accurate enough to give good results. We tried some machine-learning-like approaches, but their results (e.g. in the form of long float arrays) were not so easy to quickly compare in a large dataset. It took a lot of `Googling` (or `ChatGPTing`) to come across a scalable approach - the `Average hash` algorithm - already described above.

Looping through all the existing entries (there are more than 500_000 ordinal pictures) and comparing their content with a certain input still took a very long time in the beginning, which was not acceptable for `API`. It was really challenging to improve and optimize the algorithms, data structures and technologies used to achieve a lightning-quick result.

We also faced issues with implementing the popups, for some reason the `CSS` assigned was not working on them. It took us a decent amount of time to remember that a `JS` function had been overwriting the `CSS`. I still don't blame `JS` for this. We both agree that `CSS` is worse than `Assembly`.

## Accomplishments that we're proud of

1. **Speed of our API** - We're really proud of how fast our `API` is. We're proud of how we used `Rust` to scale our `API`. Our `API` which is public now, gives back the information in under one second.
2. **Using Machine-Learning capabilities without Machine-Learning overhead** - Yes, the algorithm again. We're super proud of how we accomplish the similarity comparison for such a large dataset at such a fast accuracy, low latency & high speed. We couldn't imagine doing this without machine learning but we did. Partial credit goes to `Hacker Factor` for talking about such a efficient technique.
3. **Successfully Integrating Hiro** - `Hiro` you're our true Hero.
4. **SEO implementation & Google Analytics** - we are proud to see our website being indexed by `Google`. The 34 distinct users of our platform make us really happy.

## What we learned

1. We recognized the incredible power of `Rust`, even in small quantities, and being callable from `python`.
2. It was also our first time doing full-fledged production deployment of a website + `API` on `HTTPS`.
3. We also learned the power of team-work and efficiently working as a team (proper task distribution, relying on each other & combined efforts).

## What's next for OrdSimilarity

1. Monetizing access to the `API` with the help of `lightning` payments.
2. Doing outreach and approaching Ordinal minting platforms with a business proposal.
3. Develop ways to add more analytics & insights about ordinals.
4. Identifying ordinals already in the `mempool`, that are not minted yet.
