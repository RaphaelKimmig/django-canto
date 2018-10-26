let initializeLibrary = function (selector, tree_url, album_url, binary_url, search_url, detail_url) {
    Vue.component('treeselect', VueTreeselect.Treeselect);

    Vue.component('search', {
        props: ['onSearch', 'query'],
        template: '<div class="search"><input autocomplete="off" type="text" name="search" v-model:value="queryState" @keyup.enter="search" /><button @click="search">Search</button></div>',
        data: function () {
            return {
                queryState: this.query,
            }
        },
        watch: {
            query: function (val) {
                this.queryState = val;
            }
        },
        methods: {
            search: function () {
                return this.onSearch(this.queryState);
            },
        },
    });
    Vue.component('item', {
        props: ["data", "previewSize"],
        template: '<div class="item" v-if="show"><a :href="detailUrl"><img :src="previewUrl" :width="previewWidth" :height="previewHeight"/>' +
            '<div class="item-details"><span class="item-name">{{ data.name }}</span><span class="item-format">{{ imageWidth }}x{{ imageHeight }}</span></div></a></div>',
        computed: {
            show: function () {
                return this.data && this.data.url && this.data.url.preview && this.data.scheme === 'image'
            },
            previewUrl: function () {
                let url = binary_url.replace("URL-PLACEHOLDER", this.data.url.preview);
                if(!url.endsWith('/')) {
                    url += '/'
                }
                url += this.previewSize;
                return url
            },
            detailUrl: function () {
                return detail_url.replace("ID-PLACEHOLDER", this.data.id)
            },
            imageWidth: function () {
                return parseInt(this.data.width, 10);
            },
            imageHeight: function () {
                return parseInt(this.data.height, 10);
            },
            previewWidth: function () {
                if (this.imageWidth > this.imageHeight) {
                    return this.previewSize;
                }
                return this.imageWidth / this.imageHeight * this.previewSize;
            },
            previewHeight: function () {
                if (this.imageHeight > this.imageWidth) {
                    return this.previewSize;
                }
                return this.imageHeight / this.imageWidth * this.previewSize;
            }
        }
    });
    Vue.component('results', {
        props: ["url"],
        data: function () {
            return {
                results: null,
            }
        },
        template: ''+
            '<div class="results" v-if="url">' +
            '<div v-if="url && !results" class="spinner"></div>' +
            '<div v-if="results" class="results-list">' +
            '<item v-for="item in results.results" :key="item.id" :data="item" :previewSize="400"></item>' +
            '</div>' +
            '<div v-if="results && results.found" class="pagination">' +
            '<a href="#" v-if="hasPreviousPage" @click="goToPreviousPage">&nbsp;&laquo;&nbsp;</a>' +
            '<span>Page {{ page }} of {{ numPages }}</span>' +
            '<a href="#" v-if="hasNextPage" @click="goToNextPage">&nbsp;&raquo;&nbsp;</a>' +
            '</div>' +
            '<div class="pagination" v-if="results && !results.found"><strong>No results found</strong></div>' +
            '</div>',
        watch: {
            url: function (val) {
                if (!!val) {
                    this.loadUrl(val);
                } else {
                    this.results = null
                }
            }
        },
        computed: {
            start: function () {
                return this.results.start || 0;
            },
            page: function () {
                return Math.floor(this.start / this.limit) + 1;
            },
            numPages: function () {
                return Math.ceil(this.found / this.limit);
            },
            limit: function () {
                return this.results.limit
            },
            found: function () {
                return this.results.found
            },
            hasNextPage: function () {
                return this.results && this.found > this.start + this.limit;
            },
            hasPreviousPage: function () {
                return this.results && this.start > 0;
            }

        },
        methods: {
            loadUrl: function (url) {
                this.results = null;
                let that = this;
                fetch(url)
                    .then(function(response) {
                        return response.json();
                    }).then(function (response_json) {
                    that.results = response_json;
                });
            },
            goToNextPage: function () {
                let url = this.url + '?start=' + (this.start + this.limit);
                this.loadUrl(url);
            },
            goToPreviousPage: function () {
                let url = this.url + '?start=' + Math.max(this.start - this.limit, 0);
                this.loadUrl(url);
            }
        }

    });
    var library = new Vue({
        el: selector,
        template: '<div class="library">' +
            '<h2 class="tree-label">Select an album</h2>\n' +
            '<treeselect\n' +
            ':multiple="false"\n' +
            ':normalizer="normalizeTreeNode"\n' +
            ':options="tree"\n' +
            ':disable-branch-nodes="true"\n' +
            'placeholder="Select an album"\n' +
            ':value="selectedAlbumId"' +
            '@input="onAlbumSelect"'+
            '></treeselect>\n' +
            '<h2 class="search-label">Search</h2>\n' +
            '<search :query="query" :on-search="onSearch"></search>\n' +
            '<results :url="resultsUrl"></results>\n' +
            '</div>',
        data: {
            selectedAlbumId: null,
            tree: null,
            query: null,
            resultsUrl: null,
        },
        created: function () {
            let that = this;
            fetch(tree_url).then(function (response) {
                return response.json();
            }).then(function (data) {
                that.tree = data.results;
            })
        },
        methods: {
            buildResultsUrl: function () {
                if(this.selectedAlbumId !== null && this.selectedAlbumId !== undefined) {
                    return album_url.replace("ID-PLACEHOLDER", this.selectedAlbumId);
                }
                if(this.query !== null && this.query !== undefined) {
                    return search_url.replace("QUERY-PLACEHOLDER", this.query);
                }
                return null;
            },
            onSearch: function (query) {
                this.selectedAlbumId = null;
                if(query.length > 0) {
                    this.query = query;
                } else {
                    this.query = null;
                }
                this.resultsUrl = this.buildResultsUrl();
            },
            onAlbumSelect: function (id) {
                this.selectedAlbumId = id;
                if(id !== null && id !== undefined) {
                    this.query = null;
                }
                this.resultsUrl = this.buildResultsUrl();
            },
            normalizeTreeNode: function normalizeTreeNode(node) {
                let label = node.name;
                if(node.scheme === 'album') {
                    label = "📷 " + node.name;
                }
                // do not allow selecting empty albums or empty categories
                let isDisabled = (
                    (node.scheme !== 'album' && (node.children === undefined || node.children.length === 0))
                    || (node.scheme === 'album' && node.size === "0")
                );

                return {id: node.id, label: label, children: node.children, isDisabled: isDisabled}
            }
        },

    })
};
