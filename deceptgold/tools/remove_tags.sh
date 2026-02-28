KEEP="v0.1.140"

for tag in $(git tag); do
  if [ "$tag" != "$KEEP" ]; then
    echo "Deleting local tag: $tag"
    git tag -d "$tag"
  else
    echo "Keeping tag: $tag"
  fi
done

for tag in $(git ls-remote --tags origin | awk '{print $2}' | sed 's|refs/tags/||' | sort -u); do
  if [ "$tag" != "$KEEP" ]; then
    echo "Deleting remote tag: $tag"
    git push origin :refs/tags/"$tag"
  else
    echo "Keeping remote tag: $tag"
  fi
done