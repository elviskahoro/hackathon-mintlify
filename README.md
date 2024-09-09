# Blog Post Generator for PRs

This GitHub Action automatically generates a blog post summarizing a Pull Request (PR) using the Claude API. The action collects relevant PR information such as the title, description, commits, contributors, and code changes, and sends this data to Claude to create a concise and detailed blog post, which is then posted as a comment on the PR.

## How it Works

The workflow is triggered when a PR is opened, edited, or synchronized. It performs the following steps:

1. **Checkout Code**: The repository code is checked out using `actions/checkout@v3`.
2. **Collect PR Information**: The action extracts the PR title, body, commits, and performs a git diff to capture the code changes between branches.
3. **Generate Blog Post with Claude**: The extracted information is sent to the Claude API to generate a blog post.
4. **Post Blog Summary**: The generated blog post is posted as a comment on the PR.

## Prerequisites

- A valid Claude API key must be set in the repository secrets as `CLAUDE_API_KEY`.
- GitHub token permissions should include `contents: write`, `pull-requests: write`, and `issues: write`.

## Example


https://github.com/elviskahoro/mintlify-hackathon/pull/12#issuecomment-2336839118

https://github.com/elviskahoro/mintlify-hackathon/pull/24#issuecomment-2337114808

