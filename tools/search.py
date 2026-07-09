from ddgs import DDGS


class SearchTool:

    def search(self, query):

        links = []

        try:
            with DDGS() as ddgs:
                results = ddgs.text(query, max_results=40)

                for r in results:
                    if "href" in r:
                        links.append(r["href"])

        except Exception:
            pass

        return links