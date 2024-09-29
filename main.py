import asyncio
import re
from crawl4ai import AsyncWebCrawler

async def main():
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(url="https://blinkit.com/prn/lays-west-indies-hot-n-sweet-chilli-flavour-potato-chips/prid/289152")

        # Find the line starting with # and store it
        markdown_content = result.markdown
        header_line = None
        for line in markdown_content.splitlines():
            line = line.strip()
            if re.match(r"^#+\s", line):
                header_line = line
                break  # Stop after finding the first header line

        # Clean the content
        start_index = markdown_content.find("My Cart")
        end_index = markdown_content.find("Disclaimer")

        if start_index != -1 and end_index != -1:
            # Remove "My Cart" from the extracted content
            cleaned_content = markdown_content[start_index + len("My Cart"):end_index] 
        else:
            cleaned_content = markdown_content  # Keep original content if markers not found

        # Add the header line to the top (if found)
        if header_line:
            final_content = header_line + "\n" + cleaned_content
        else:
            final_content = cleaned_content

        # Save the content to a markdown file
        with open("output.md", "w", encoding="utf-8") as f:
            f.write(final_content)

        # Extract and print links (with multi-line support)
        lines = final_content.splitlines()
        links = []
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            match = re.search(r"https?://[^\s\)\"]+", line)
            if match:
                link = match.group(0)
                # Check next line if the link seems incomplete (ends with '-')
                if link.endswith('-'):
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        link += next_line
                        i += 1  # Skip the next line since it's part of the link
                links.append(link)
            i += 1

        # Clean image links
        cleaned_links = []
        for link in links:
            if "cdn.grofers.com" in link:
                # Extract the relevant part of the URL
                cleaned_link = re.sub(r"https://cdn.grofers.com/cdn-cgi/image/f=auto,fit=scale-down,q=85,metadata=none,[^/]+/[^/]+/", "https://cdn.grofers.com/app/", link)
                cleaned_link = cleaned_link.replace("\\", "")  # Remove backslashes 
                cleaned_links.append(cleaned_link)
            else:
                cleaned_links.append(link) 

        print("Cleaned Links:")
        for link in cleaned_links:
            print(link)

if __name__ == "__main__":
    asyncio.run(main())