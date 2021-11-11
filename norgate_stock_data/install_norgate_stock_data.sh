
# make sure you've activated the zipline anaconda environment.

#    > zipline bundles
#    > zipline clean --bundle norgate_stock_data --before `date -d "+1 days" --iso-8601`
#    > zipline ingest --bundle norgate_stock_data


bundle_name=norgate_stock_data

# https://unix.stackexchange.com/questions/338000/bash-assign-output-of-pipe-to-a-variable
shopt -s lastpipe
echo -e "import zipline\nprint(zipline.__file__)" | python | read name

# name=`which zipline`
[ -z "${name}" ] && echo "Please make sure that you've activated the zipline conda environment, e.g. conda activate py36zl" && exit 1
name=`dirname ${name}`
name="${name}/data/bundles"
[ ! -d "${name}" ] && echo "Directory ${name} DOES NOT exists. Cannot install bundle!" && exit 1
echo ${name}

TARGET=${name}/${bundle_name}.py
[ -L "${TARGET}" ] && rm ${TARGET}

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
ln -s $DIR/${bundle_name}.py ${name}

cat << EOF > $HOME/.zipline/extension.py
from zipline.data.bundles import register, ${bundle_name}
register('${bundle_name}', ${bundle_name}.${bundle_name}, calendar_name='XNYS') #  XNYS, us_futures
EOF
