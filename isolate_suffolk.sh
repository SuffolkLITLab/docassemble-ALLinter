testseq="github.com/SuffolkLITLab/"

case $1 in
  *"$testseq"*) echo $1 && cp -r . ../../all_suffolk_data/$2 ;;
  *) :
esac
