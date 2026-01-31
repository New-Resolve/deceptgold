KEEP="v0.1.130"

for tag in $(git tag); do
  if [ "$tag" != "$KEEP" ]; then
    echo "Apagando tag local: $tag"
    git tag -d "$tag"
  else
    echo "Mantendo tag: $tag"
  fi
done



KEEP="v0.1.126"

for tag in $(git ls-remote --tags origin | awk '{print $2}' | sed 's|refs/tags/||' | sort -u); do
  if [ "$tag" != "$KEEP" ]; then
    echo "Apagando tag remota: $tag"
    git push origin :refs/tags/"$tag"
  else
    echo "Mantendo tag remota: $tag"
  fi
done