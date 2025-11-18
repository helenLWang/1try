// NailTech Pro - 主要JavaScript逻辑文件
// 穿戴甲购物网站核心功能实现

// 全局变量
let products = [];
let filteredProducts = [];
let cart = JSON.parse(localStorage.getItem('cart')) || [];
let userPreferences = JSON.parse(localStorage.getItem('userPreferences')) || {
    viewedProducts: [],
    favoriteStyles: [],
    priceRange: [0, 500]
};
let currentPage = 1;
const productsPerPage = 12;

// 商品数据模拟
const mockProducts = [
    {
        id: 1,
        name: "法式优雅穿戴甲",
        price: 89,
        originalPrice: 129,
        style: "french",
        shape: "square",
        material: "gel",
        rating: 4.8,
        reviews: 234,
        stock: 15,
        image: "https://kimi-web-img.moonshot.cn/img/prestigiousnailsalon.com/50f7b8ac424ec93c8db81136a7c982a088367f50.jpg",
        description: "经典法式美甲设计，采用高品质凝胶材质，持久耐用",
        features: ["持久14天", "易贴合", "自然外观"],
        isNew: true,
        isHot: false
    },
    {
        id: 2,
        name: "闪粉派对穿戴甲",
        price: 69,
        originalPrice: 99,
        style: "glitter",
        shape: "almond",
        material: "acrylic",
        rating: 4.6,
        reviews: 156,
        stock: 8,
        image: "https://kimi-web-img.moonshot.cn/img/easyday.snydle.com/0de43f5b5cc5b191e8f70bb140b93ce4b132d74d.jpg",
        description: "闪耀的闪粉设计，完美适合派对和特殊场合",
        features: ["闪耀效果", "派对必备", "多色可选"],
        isNew: false,
        isHot: true
    },
    {
        id: 3,
        name: "简约果冻穿戴甲",
        price: 59,
        originalPrice: 79,
        style: "minimal",
        shape: "round",
        material: "gel",
        rating: 4.7,
        reviews: 189,
        stock: 23,
        image: "https://kimi-web-img.moonshot.cn/img/auroracos.com/d8bdfb2ab7df6c46f5979e4ff253f5923a5cd484.jpg",
        description: "简约而不简单的果冻质感，日常通勤必备",
        features: ["果冻质感", "日常百搭", "舒适贴合"],
        isNew: false,
        isHot: false
    },
    {
        id: 4,
        name: "花卉艺术穿戴甲",
        price: 99,
        originalPrice: 139,
        style: "floral",
        shape: "almond",
        material: "press-on",
        rating: 4.9,
        reviews: 312,
        stock: 12,
        image: "https://kimi-web-img.moonshot.cn/img/img.allw.mn/374acc7026683c10f958260580e29d38eebcc762.jpg",
        description: "精致花卉图案设计，展现女性优雅气质",
        features: ["手工绘制", "花卉图案", "优雅设计"],
        isNew: true,
        isHot: true
    },
    {
        id: 5,
        name: "金属质感穿戴甲",
        price: 79,
        originalPrice: 109,
        style: "minimal",
        shape: "stiletto",
        material: "acrylic",
        rating: 4.5,
        reviews: 98,
        stock: 18,
        image: "https://kimi-web-img.moonshot.cn/img/s3-media0.fl.yelpcdn.com/22bcb11e2be668e0694dbdcb1f57523cebf0602a.jpg",
        description: "时尚金属质感，打造前卫个性的美甲造型",
        features: ["金属质感", "前卫设计", "个性十足"],
        isNew: false,
        isHot: false
    },
    {
        id: 6,
        name: "渐变色穿戴甲",
        price: 85,
        originalPrice: 115,
        style: "glitter",
        shape: "square",
        material: "gel",
        rating: 4.7,
        reviews: 167,
        stock: 21,
        image: "https://kimi-web-img.moonshot.cn/img/shopack.pk/f9149887c22c3a1ccfa4cca1f2f93decff3ac71a.jpg",
        description: "梦幻渐变色系，从深到浅的自然过渡",
        features: ["渐变色彩", "梦幻效果", "多色可选"],
        isNew: true,
        isHot: false
    },
    {
        id: 7,
        name: "珍珠装饰穿戴甲",
        price: 129,
        originalPrice: 169,
        style: "french",
        shape: "almond",
        material: "gel",
        rating: 4.8,
        reviews: 203,
        stock: 6,
        image: "https://kimi-web-img.moonshot.cn/img/ladylife.style/32507fa26b30c6fd6a47c162bd09ce58cd21dc70.jpg",
        description: "珍珠装饰点缀，高贵典雅的法式设计",
        features: ["珍珠装饰", "高贵典雅", "法式经典"],
        isNew: false,
        isHot: true
    },
    {
        id: 8,
        name: "彩虹糖果穿戴甲",
        price: 65,
        originalPrice: 89,
        style: "glitter",
        shape: "round",
        material: "press-on",
        rating: 4.6,
        reviews: 134,
        stock: 28,
        image: "https://kimi-web-img.moonshot.cn/img/ladylife.style/f6b811e27ac348963607985ea124e2be290762ac.jpg",
        description: "多彩糖果色系，甜美可爱的少女风格",
        features: ["彩虹色彩", "甜美可爱", "少女风格"],
        isNew: true,
        isHot: false
    },
    {
        id: 9,
        name: "几何图案穿戴甲",
        price: 75,
        originalPrice: 105,
        style: "minimal",
        shape: "square",
        material: "acrylic",
        rating: 4.4,
        reviews: 87,
        stock: 16,
        image: "https://kimi-web-img.moonshot.cn/img/m.media-amazon.com/9fc1b4a5b02e5382ccac7b4d00b463ddcaeeb200.jpg",
        description: "现代几何图案设计，简约而富有设计感",
        features: ["几何图案", "现代设计", "简约时尚"],
        isNew: false,
        isHot: false
    },
    {
        id: 10,
        name: "星空闪烁穿戴甲",
        price: 95,
        originalPrice: 125,
        style: "glitter",
        shape: "stiletto",
        material: "gel",
        rating: 4.9,
        reviews: 278,
        stock: 9,
        image: "https://kimi-web-img.moonshot.cn/img/ladylife.style/8c1e9cadc7c42f2c4f244572bc58dcf6bd52bc25.jpg",
        description: "星空主题设计，闪烁如星辰般璀璨",
        features: ["星空主题", "闪烁效果", "璀璨夺目"],
        isNew: true,
        isHot: true
    },
    {
        id: 11,
        name: "大理石纹穿戴甲",
        price: 88,
        originalPrice: 118,
        style: "minimal",
        shape: "almond",
        material: "gel",
        rating: 4.7,
        reviews: 145,
        stock: 19,
        image: "https://kimi-web-img.moonshot.cn/img/media.karousell.com/8122e2dc6fceeb7bd370dffeb9635bd60e80172f.jpg",
        description: "大理石纹理设计，高级感十足的自然美感",
        features: ["大理石纹", "高级感", "自然美感"],
        isNew: false,
        isHot: false
    },
    {
        id: 12,
        name: "蝴蝶装饰穿戴甲",
        price: 108,
        originalPrice: 148,
        style: "floral",
        shape: "round",
        material: "press-on",
        rating: 4.8,
        reviews: 196,
        stock: 14,
        image: "https://kimi-web-img.moonshot.cn/img/app.dropinblog.com/b328ba40d40b1df612b4505d2faa12c28ba66158.jpg",
        description: "蝴蝶装饰设计，浪漫唯美的仙女风格",
        features: ["蝴蝶装饰", "浪漫唯美", "仙女风格"],
        isNew: true,
        isHot: false
    },
    {
        id: 13,
        name: "霓虹色彩穿戴甲",
        price: 72,
        originalPrice: 98,
        style: "glitter",
        shape: "square",
        material: "acrylic",
        rating: 4.5,
        reviews: 112,
        stock: 25,
        image: "https://kimi-web-img.moonshot.cn/img/m.media-amazon.com/f35b72bf5f2196a5769c689f47478dd4299f1326.jpg",
        description: "霓虹色彩设计，充满活力的年轻风格",
        features: ["霓虹色彩", "充满活力", "年轻风格"],
        isNew: false,
        isHot: false
    },
    {
        id: 14,
        name: "蕾丝花边穿戴甲",
        price: 118,
        originalPrice: 158,
        style: "french",
        shape: "almond",
        material: "gel",
        rating: 4.9,
        reviews: 234,
        stock: 11,
        image: "https://kimi-web-img.moonshot.cn/img/i.ebayimg.com/1f9dcfdf84b1d598ebfbb2510588a60126f3146d.jpg",
        description: "蕾丝花边装饰，精致的法式浪漫风格",
        features: ["蕾丝花边", "精致工艺", "法式浪漫"],
        isNew: true,
        isHot: true
    },
    {
        id: 15,
        name: "磨砂质感穿戴甲",
        price: 82,
        originalPrice: 112,
        style: "minimal",
        shape: "stiletto",
        material: "press-on",
        rating: 4.6,
        reviews: 123,
        stock: 17,
        image: "https://kimi-web-img.moonshot.cn/img/meteorbeauty.com/d2f32a780760797466cc8058b168af953a108b0e.jpg",
        description: "磨砂质感设计，低调奢华的高级感",
        features: ["磨砂质感", "低调奢华", "高级感"],
        isNew: false,
        isHot: false
    },
    {
        id: 16,
        name: "水晶装饰穿戴甲",
        price: 138,
        originalPrice: 178,
        style: "french",
        shape: "round",
        material: "gel",
        rating: 4.8,
        reviews: 189,
        stock: 7,
        image: "https://kimi-web-img.moonshot.cn/img/www.wikihow.com/b806f053f5ff6e5d73876de2bfc6b3e2598e9788.jpg",
        description: "水晶装饰点缀，璀璨夺目的奢华设计",
        features: ["水晶装饰", "璀璨夺目", "奢华设计"],
        isNew: true,
        isHot: true
    },
    {
        id: 17,
        name: "动物纹理穿戴甲",
        price: 91,
        originalPrice: 121,
        style: "minimal",
        shape: "almond",
        material: "acrylic",
        rating: 4.4,
        reviews: 96,
        stock: 13,
        image: "https://kimi-web-img.moonshot.cn/img/soprettynails.com.au/a717ae716a5d412f59aa5f43757dc8eb1a7cd441.jpg",
        description: "动物纹理设计，野性时尚的个性表达",
        features: ["动物纹理", "野性时尚", "个性表达"],
        isNew: false,
        isHot: false
    },
    {
        id: 18,
        name: "透明果冻穿戴甲",
        price: 56,
        originalPrice: 76,
        style: "minimal",
        shape: "square",
        material: "gel",
        rating: 4.7,
        reviews: 201,
        stock: 32,
        image: "https://kimi-web-img.moonshot.cn/img/cdn.ecommercedns.uk/0246c26388f2d2828143bf64b6673450dd64defd.png",
        description: "透明果冻质感，自然清新的日常选择",
        features: ["透明质感", "自然清新", "日常百搭"],
        isNew: false,
        isHot: false
    },
    {
        id: 19,
        name: "金属链条穿戴甲",
        price: 115,
        originalPrice: 155,
        style: "minimal",
        shape: "stiletto",
        material: "gel",
        rating: 4.6,
        reviews: 134,
        stock: 10,
        image: "https://kimi-web-img.moonshot.cn/img/ladylife.style/a319107e5ae52cebd204cb3a633692c095924a4d.jpg",
        description: "金属链条装饰，朋克风格的个性设计",
        features: ["金属链条", "朋克风格", "个性十足"],
        isNew: true,
        isHot: false
    },
    {
        id: 20,
        name: "彩虹渐变穿戴甲",
        price: 78,
        originalPrice: 108,
        style: "glitter",
        shape: "round",
        material: "press-on",
        rating: 4.8,
        reviews: 167,
        stock: 22,
        image: "https://kimi-web-img.moonshot.cn/img/meteorbeauty.com/2073464ddabf6cec1b9215d64c84a8da4fe81427.jpg",
        description: "彩虹渐变色彩，甜美梦幻的少女心事",
        features: ["彩虹渐变", "甜美梦幻", "少女心"],
        isNew: false,
        isHot: true
    },
    {
        id: 21,
        name: "极光色彩穿戴甲",
        price: 103,
        originalPrice: 133,
        style: "glitter",
        shape: "almond",
        material: "gel",
        rating: 4.9,
        reviews: 245,
        stock: 8,
        image: "https://kimi-web-img.moonshot.cn/img/moyou.co.uk/1f6957f28570469ebce0bf56e0e4428bf15063c3.jpg",
        description: "极光色彩效果，如北极光般绚烂多彩",
        features: ["极光效果", "绚烂多彩", "独特设计"],
        isNew: true,
        isHot: true
    },
    {
        id: 22,
        name: "贝壳光泽穿戴甲",
        price: 87,
        originalPrice: 117,
        style: "minimal",
        shape: "square",
        material: "acrylic",
        rating: 4.5,
        reviews: 118,
        stock: 20,
        image: "https://kimi-web-img.moonshot.cn/img/cdn.tatlerasia.com/08f701d10c3feed506f077faf684226cef396e82.jpg",
        description: "贝壳光泽质感，如珍珠般温润优雅",
        features: ["贝壳光泽", "珍珠质感", "温润优雅"],
        isNew: false,
        isHot: false
    },
    {
        id: 23,
        name: "涂鸦艺术穿戴甲",
        price: 93,
        originalPrice: 123,
        style: "minimal",
        shape: "round",
        material: "press-on",
        rating: 4.7,
        reviews: 152,
        stock: 15,
        image: "https://kimi-web-img.moonshot.cn/img/m.media-amazon.com/aa4a59bc8d94e4ced42968acb7947408a8c96d98.jpg",
        description: "涂鸦艺术图案，充满创意的个性表达",
        features: ["涂鸦艺术", "创意十足", "个性表达"],
        isNew: true,
        isHot: false
    },
    {
        id: 24,
        name: "丝绒质感穿戴甲",
        price: 106,
        originalPrice: 136,
        style: "minimal",
        shape: "almond",
        material: "gel",
        rating: 4.8,
        reviews: 178,
        stock: 12,
        image: "https://kimi-web-img.moonshot.cn/img/img.allw.mn/78c9c152c1be375110533bd6c1fa14aa85eab337.jpg",
        description: "丝绒质感设计，温暖舒适的秋冬必备",
        features: ["丝绒质感", "温暖舒适", "秋冬必备"],
        isNew: false,
        isHot: true
    }
];

// 初始化函数
function initializeApp() {
    products = [...mockProducts];
    filteredProducts = [...products];
    
    // 初始化各个组件
    initializeParticles();
    initializeCarousel();
    initializeFilters();
    initializeSearch();
    initializeCart();
    initializeAnimations();
    initializeRecommendations();
    
    // 渲染商品
    renderProducts();
    updateCartCount();
    
    // 绑定事件监听器
    bindEventListeners();
    
    console.log('NailTech Pro 应用初始化完成');
}

// 粒子背景效果
function initializeParticles() {
    const sketch = (p) => {
        let particles = [];
        
        p.setup = () => {
            const canvas = p.createCanvas(p.windowWidth, p.windowHeight);
            canvas.parent('particles-container');
            
            // 创建粒子
            for (let i = 0; i < 50; i++) {
                particles.push({
                    x: p.random(p.width),
                    y: p.random(p.height),
                    size: p.random(2, 6),
                    speedX: p.random(-0.5, 0.5),
                    speedY: p.random(-0.5, 0.5),
                    opacity: p.random(0.1, 0.3)
                });
            }
        };
        
        p.draw = () => {
            p.clear();
            
            // 绘制粒子
            particles.forEach(particle => {
                p.fill(232, 180, 184, particle.opacity * 255);
                p.noStroke();
                p.circle(particle.x, particle.y, particle.size);
                
                // 更新位置
                particle.x += particle.speedX;
                particle.y += particle.speedY;
                
                // 边界检测
                if (particle.x < 0 || particle.x > p.width) particle.speedX *= -1;
                if (particle.y < 0 || particle.y > p.height) particle.speedY *= -1;
            });
        };
        
        p.windowResized = () => {
            p.resizeCanvas(p.windowWidth, p.windowHeight);
        };
    };
    
    new p5(sketch);
}

// 轮播图初始化
function initializeCarousel() {
    const splide = new Splide('#hero-carousel', {
        type: 'loop',
        autoplay: true,
        interval: 4000,
        pauseOnHover: true,
        arrows: false,
        pagination: true,
        easing: 'cubic-bezier(0.25, 1, 0.5, 1)'
    });
    
    splide.mount();
}

// 筛选功能初始化
function initializeFilters() {
    const filterChips = document.querySelectorAll('.filter-chip');
    let activeFilters = {
        style: 'all',
        shape: 'all',
        material: 'all'
    };
    
    filterChips.forEach(chip => {
        chip.addEventListener('click', () => {
            const filterType = chip.dataset.filter;
            const filterValue = chip.dataset.value;
            
            // 更新活动筛选器
            activeFilters[filterType] = filterValue;
            
            // 更新UI
            filterChips.forEach(c => {
                if (c.dataset.filter === filterType) {
                    c.classList.remove('active');
                }
            });
            chip.classList.add('active');
            
            // 应用筛选
            applyFilters(activeFilters);
        });
    });
    
    // 设置默认选中状态
    document.querySelector('[data-filter="style"][data-value="all"]').classList.add('active');
    document.querySelector('[data-filter="shape"][data-value="all"]').classList.add('active');
    document.querySelector('[data-filter="material"][data-value="all"]').classList.add('active');
}

// 应用筛选器
function applyFilters(filters) {
    filteredProducts = products.filter(product => {
        const styleMatch = filters.style === 'all' || product.style === filters.style;
        const shapeMatch = filters.shape === 'all' || product.shape === filters.shape;
        const materialMatch = filters.material === 'all' || product.material === filters.material;
        
        return styleMatch && shapeMatch && materialMatch;
    });
    
    currentPage = 1;
    renderProducts();
    
    // 更新商品计数
    document.getElementById('product-count').textContent = filteredProducts.length;
}

// 搜索功能初始化
function initializeSearch() {
    const searchInput = document.getElementById('search-input');
    const searchBtn = document.getElementById('search-btn');
    
    let searchTimeout;
    
    searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            performSearch(e.target.value);
        }, 300);
    });
    
    searchBtn.addEventListener('click', () => {
        performSearch(searchInput.value);
    });
}

// 执行搜索
function performSearch(query) {
    if (!query.trim()) {
        filteredProducts = [...products];
    } else {
        const searchTerm = query.toLowerCase();
        filteredProducts = products.filter(product => 
            product.name.toLowerCase().includes(searchTerm) ||
            product.description.toLowerCase().includes(searchTerm) ||
            product.features.some(feature => feature.toLowerCase().includes(searchTerm))
        );
    }
    
    currentPage = 1;
    renderProducts();
    document.getElementById('product-count').textContent = filteredProducts.length;
}

// 购物车功能初始化
function initializeCart() {
    updateCartCount();
}

// 渲染商品列表
function renderProducts() {
    const grid = document.getElementById('products-grid');
    const startIndex = (currentPage - 1) * productsPerPage;
    const endIndex = startIndex + productsPerPage;
    const productsToShow = filteredProducts.slice(0, endIndex);
    
    grid.innerHTML = '';
    
    productsToShow.forEach((product, index) => {
        const productCard = createProductCard(product);
        grid.appendChild(productCard);
        
        // 添加进入动画
        anime({
            targets: productCard,
            opacity: [0, 1],
            translateY: [30, 0],
            delay: index * 100,
            duration: 600,
            easing: 'easeOutCubic'
        });
    });
    
    // 更新加载更多按钮
    const loadMoreBtn = document.getElementById('load-more-btn');
    if (endIndex >= filteredProducts.length) {
        loadMoreBtn.style.display = 'none';
    } else {
        loadMoreBtn.style.display = 'block';
    }
}

// 创建商品卡片
function createProductCard(product) {
    const card = document.createElement('div');
    card.className = 'card-hover bg-white rounded-2xl shadow-lg overflow-hidden group cursor-pointer';
    
    const discount = Math.round(((product.originalPrice - product.price) / product.originalPrice) * 100);
    
    card.innerHTML = `
        <div class="relative">
            <img src="${product.image}" alt="${product.name}" class="w-full h-48 object-cover group-hover:scale-105 transition-transform duration-300">
            
            ${product.isNew ? '<span class="absolute top-2 left-2 bg-green-500 text-white text-xs px-2 py-1 rounded-full">新品</span>' : ''}
            ${product.isHot ? '<span class="absolute top-2 right-2 bg-red-500 text-white text-xs px-2 py-1 rounded-full">热销</span>' : ''}
            
            <div class="absolute top-2 right-2 bg-red-500 text-white text-xs px-2 py-1 rounded-full">
                -${discount}%
            </div>
            
            <div class="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 transition-opacity duration-300 flex items-center justify-center">
                <button class="add-to-cart-btn opacity-0 group-hover:opacity-100 bg-white text-gray-800 px-4 py-2 rounded-full font-semibold transform translate-y-4 group-hover:translate-y-0 transition-all duration-300" data-product-id="${product.id}">
                    加入购物车
                </button>
            </div>
        </div>
        
        <div class="p-4">
            <h3 class="font-semibold text-gray-800 mb-2 line-clamp-2">${product.name}</h3>
            
            <div class="flex items-center mb-2">
                <div class="flex text-yellow-400">
                    ${generateStars(product.rating)}
                </div>
                <span class="text-sm text-gray-600 ml-2">(${product.reviews})</span>
            </div>
            
            <div class="flex items-center justify-between mb-3">
                <div class="flex items-center space-x-2">
                    <span class="price-tag px-2 py-1 rounded-full text-sm font-bold">¥${product.price}</span>
                    <span class="text-gray-400 line-through text-sm">¥${product.originalPrice}</span>
                </div>
                <span class="text-xs text-gray-500">库存: ${product.stock}</span>
            </div>
            
            <div class="flex flex-wrap gap-1 mb-3">
                ${product.features.slice(0, 2).map(feature => 
                    `<span class="bg-gray-100 text-gray-600 text-xs px-2 py-1 rounded-full">${feature}</span>`
                ).join('')}
            </div>
            
            <div class="flex space-x-2">
                <button class="flex-1 bg-pink-500 text-white py-2 rounded-lg hover:bg-pink-600 transition-colors text-sm font-medium" onclick="viewProduct(${product.id})">
                    查看详情
                </button>
                <button class="ar-try-btn px-3 py-2 border border-pink-500 text-pink-500 rounded-lg hover:bg-pink-50 transition-colors text-sm" data-product-id="${product.id}">
                    AR试戴
                </button>
            </div>
        </div>
    `;
    
    return card;
}

// 生成星级评分
function generateStars(rating) {
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 !== 0;
    let stars = '';
    
    for (let i = 0; i < fullStars; i++) {
        stars += '<svg class="w-4 h-4 fill-current" viewBox="0 0 20 20"><path d="M10 15l-5.878 3.09 1.123-6.545L.489 6.91l6.572-.955L10 0l2.939 5.955 6.572.955-4.756 4.635 1.123 6.545z"/></svg>';
    }
    
    if (hasHalfStar) {
        stars += '<svg class="w-4 h-4 fill-current" viewBox="0 0 20 20"><path d="M10 15l-5.878 3.09 1.123-6.545L.489 6.91l6.572-.955L10 0v15z"/></svg>';
    }
    
    const emptyStars = 5 - Math.ceil(rating);
    for (let i = 0; i < emptyStars; i++) {
        stars += '<svg class="w-4 h-4 text-gray-300 fill-current" viewBox="0 0 20 20"><path d="M10 15l-5.878 3.09 1.123-6.545L.489 6.91l6.572-.955L10 0l2.939 5.955 6.572.955-4.756 4.635 1.123 6.545z"/></svg>';
    }
    
    return stars;
}

// 初始化动画效果
function initializeAnimations() {
    // 标题文字动画
    Splitting();
    
    anime({
        targets: '.hero-title .char',
        opacity: [0, 1],
        translateY: [50, 0],
        delay: anime.stagger(100),
        duration: 800,
        easing: 'easeOutCubic'
    });
    
    // 技术特色标签动画
    anime({
        targets: '.tech-badge',
        opacity: [0, 1],
        scale: [0.8, 1],
        delay: anime.stagger(200, {start: 1000}),
        duration: 600,
        easing: 'easeOutBack'
    });
}

// 初始化推荐系统
function initializeRecommendations() {
    const recommendedProducts = getRecommendedProducts();
    renderRecommendations(recommendedProducts);
}

// 获取推荐商品
function getRecommendedProducts() {
    // 基于用户偏好和商品热度进行推荐
    const viewedProducts = userPreferences.viewedProducts;
    const favoriteStyles = userPreferences.favoriteStyles;
    
    let recommendations = [];
    
    // 基于浏览历史的推荐
    if (viewedProducts.length > 0) {
        const lastViewed = viewedProducts[viewedProducts.length - 1];
        const lastProduct = products.find(p => p.id === lastViewed);
        if (lastProduct) {
            const similarProducts = products.filter(p => 
                p.id !== lastViewed && 
                (p.style === lastProduct.style || p.shape === lastProduct.shape)
            );
            recommendations.push(...similarProducts.slice(0, 3));
        }
    }
    
    // 基于热门商品的推荐
    const hotProducts = products.filter(p => p.isHot).slice(0, 3);
    recommendations.push(...hotProducts);
    
    // 基于新品的推荐
    const newProducts = products.filter(p => p.isNew).slice(0, 2);
    recommendations.push(...newProducts);
    
    // 去重并限制数量
    const uniqueRecommendations = recommendations.filter((product, index, self) => 
        index === self.findIndex(p => p.id === product.id)
    );
    
    return uniqueRecommendations.slice(0, 8);
}

// 渲染推荐商品
function renderRecommendations(recommendations) {
    const slider = document.getElementById('recommendation-slider');
    slider.innerHTML = '';
    
    recommendations.forEach((product, index) => {
        const card = document.createElement('div');
        card.className = 'flex-shrink-0 w-64 bg-white rounded-xl shadow-lg overflow-hidden';
        
        card.innerHTML = `
            <div class="relative">
                <img src="${product.image}" alt="${product.name}" class="w-full h-40 object-cover">
                <div class="absolute top-2 right-2 bg-red-500 text-white text-xs px-2 py-1 rounded-full">
                    推荐
                </div>
            </div>
            <div class="p-4">
                <h4 class="font-semibold text-gray-800 mb-2 line-clamp-1">${product.name}</h4>
                <div class="flex items-center justify-between">
                    <span class="price-tag px-2 py-1 rounded-full text-sm font-bold">¥${product.price}</span>
                    <button class="bg-pink-500 text-white px-3 py-1 rounded-full text-sm hover:bg-pink-600 transition-colors" onclick="addToCart(${product.id})">
                        加入购物车
                    </button>
                </div>
            </div>
        `;
        
        slider.appendChild(card);
        
        // 添加进入动画
        anime({
            targets: card,
            opacity: [0, 1],
            translateX: [50, 0],
            delay: index * 150,
            duration: 600,
            easing: 'easeOutCubic'
        });
    });
}

// 绑定事件监听器
function bindEventListeners() {
    // 加载更多按钮
    document.getElementById('load-more-btn').addEventListener('click', () => {
        currentPage++;
        renderProducts();
    });
    
    // 排序选择
    document.getElementById('sort-select').addEventListener('change', (e) => {
        sortProducts(e.target.value);
    });
    
    // 推荐滑块控制
    document.getElementById('slider-prev').addEventListener('click', () => {
        const slider = document.getElementById('recommendation-slider');
        slider.scrollBy({ left: -300, behavior: 'smooth' });
    });
    
    document.getElementById('slider-next').addEventListener('click', () => {
        const slider = document.getElementById('recommendation-slider');
        slider.scrollBy({ left: 300, behavior: 'smooth' });
    });
    
    // 购物车按钮
    document.getElementById('cart-btn').addEventListener('click', () => {
        window.location.href = 'cart.html';
    });
    
    // CTA按钮
    document.getElementById('explore-btn').addEventListener('click', () => {
        document.querySelector('#products-grid').scrollIntoView({ behavior: 'smooth' });
    });
    
    document.getElementById('ar-demo-btn').addEventListener('click', () => {
        alert('AR试戴功能演示：请使用移动设备摄像头体验虚拟试戴效果');
    });
    
    // 移动端菜单
    document.getElementById('mobile-menu-btn').addEventListener('click', () => {
        alert('移动端菜单功能');
    });
    
    // 事件委托处理商品卡片交互
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('add-to-cart-btn')) {
            const productId = parseInt(e.target.dataset.productId);
            addToCart(productId);
        }
        
        if (e.target.classList.contains('ar-try-btn')) {
            const productId = parseInt(e.target.dataset.productId);
            arTryOn(productId);
        }
    });
}

// 商品排序
function sortProducts(sortType) {
    switch (sortType) {
        case 'price-low':
            filteredProducts.sort((a, b) => a.price - b.price);
            break;
        case 'price-high':
            filteredProducts.sort((a, b) => b.price - a.price);
            break;
        case 'rating':
            filteredProducts.sort((a, b) => b.rating - a.rating);
            break;
        case 'newest':
            filteredProducts.sort((a, b) => b.isNew - a.isNew);
            break;
        default:
            filteredProducts = [...products];
    }
    
    currentPage = 1;
    renderProducts();
}

// 添加到购物车
function addToCart(productId) {
    const product = products.find(p => p.id === productId);
    if (!product) return;
    
    const existingItem = cart.find(item => item.id === productId);
    
    if (existingItem) {
        existingItem.quantity += 1;
    } else {
        cart.push({
            ...product,
            quantity: 1
        });
    }
    
    localStorage.setItem('cart', JSON.stringify(cart));
    updateCartCount();
    
    // 显示添加成功提示
    showNotification('商品已添加到购物车', 'success');
    
    // 更新用户偏好
    updateUserPreferences('cart', product);
}

// 更新购物车数量
function updateCartCount() {
    const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);
    document.getElementById('cart-count').textContent = totalItems;
}

// 查看商品详情
function viewProduct(productId) {
    // 记录浏览历史
    updateUserPreferences('view', products.find(p => p.id === productId));
    
    // 跳转到商品详情页
    window.location.href = `product-detail.html?id=${productId}`;
}

// AR试戴功能
function arTryOn(productId) {
    const product = products.find(p => p.id === productId);
    if (!product) return;
    
    // 模拟AR试戴体验
    showNotification(`正在启动AR试戴：${product.name}`, 'info');
    
    // 这里可以集成真实的AR SDK
    setTimeout(() => {
        alert(`AR试戴功能演示\n\n产品：${product.name}\n颜色：多色可选\n建议使用移动设备获得最佳体验`);
    }, 1000);
    
    // 更新用户偏好
    updateUserPreferences('ar_try', product);
}

// 更新用户偏好
function updateUserPreferences(action, product) {
    switch (action) {
        case 'view':
            if (!userPreferences.viewedProducts.includes(product.id)) {
                userPreferences.viewedProducts.push(product.id);
                if (userPreferences.viewedProducts.length > 20) {
                    userPreferences.viewedProducts.shift();
                }
            }
            break;
        case 'cart':
            if (!userPreferences.favoriteStyles.includes(product.style)) {
                userPreferences.favoriteStyles.push(product.style);
            }
            break;
        case 'ar_try':
            // 记录AR试戴偏好
            break;
    }
    
    localStorage.setItem('userPreferences', JSON.stringify(userPreferences));
}

// 显示通知
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `fixed top-20 right-4 z-50 px-6 py-3 rounded-lg shadow-lg text-white font-medium transform translate-x-full transition-transform duration-300`;
    
    switch (type) {
        case 'success':
            notification.classList.add('bg-green-500');
            break;
        case 'error':
            notification.classList.add('bg-red-500');
            break;
        case 'warning':
            notification.classList.add('bg-yellow-500');
            break;
        default:
            notification.classList.add('bg-blue-500');
    }
    
    notification.textContent = message;
    document.body.appendChild(notification);
    
    // 显示动画
    setTimeout(() => {
        notification.classList.remove('translate-x-full');
    }, 100);
    
    // 自动隐藏
    setTimeout(() => {
        notification.classList.add('translate-x-full');
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', initializeApp);

// 导出函数供其他页面使用
window.NailTechApp = {
    addToCart,
    viewProduct,
    arTryOn,
    showNotification,
    updateUserPreferences
};