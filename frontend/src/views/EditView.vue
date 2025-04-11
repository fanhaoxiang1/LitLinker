<template>
    <div id="app">
        <header>
            <ul>
                <li id="selected">跨学科阅读作业设计工具</li>
                <!-- <li>大纲编辑</li> -->
            </ul>
        </header>
        <!-- <div class="nav">
            <el-breadcrumb separator=">">
                <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
                <el-breadcrumb-item>课程创建</el-breadcrumb-item>
            </el-breadcrumb>
        </div> -->

        <div class="mainx">
            <el-row :gutter="30">
                <el-col :span="10" class="exist-space">
                    <div v-if="isConfigOpen">
                        <div class="section">
                            <h3>感兴趣的学科或主题</h3>
                            <el-checkbox-group v-model="selectedSubjects" class="bordered-checkboxes">
                                <el-checkbox v-for="subject in subjects" :key="subject" :label="subject"
                                    border></el-checkbox>
                            </el-checkbox-group>
                            <!-- <el-button @click="getCases" style="margin-top: 20px;" type="primary">确认</el-button> -->
                        </div>
                    </div>

                    <div class="section" v-if="isConfigOpen">
                        <h3>选择课文范围</h3>
                        <el-transfer v-model="textTitles" :data="textList" :titles="['课文标题', '已选']" filterable
                            style="text-align: center; " />
                        <!-- <el-button @click="getTextSet" type="primary" v-if="isConfigOpen"
                            style="margin-top: 20px;">选定课文</el-button> -->
                        <div>
                            <el-button @click="textTitles = [14,16,51,70,92,96,97,101];" type="plain" style="margin-top: 30px;">设置为“综合实践”课文</el-button>
                            <el-button @click="textTitles = [7,22,30,39,58,98,99,100];" type="plain" style="margin-top: 30px;">设置为“传统学科”课文</el-button>
                        </div>
                            <hr />

                    </div>
                    <div class="config-button-container">
                        <el-button @click="analyseAndRankCases" type="primary" v-if="isConfigOpen">推荐主题</el-button>
                        <el-button @click="isConfigOpen = !isConfigOpen" class="config-button">隐藏 / 显示基本设置</el-button>
                    </div>
                    <div class="section">
                        <div class="card-title-header">
                            <h2>可能的主题</h2>
                            <!-- 手动添加案例按钮，触发弹出窗口 -->
                            <el-button type="warning" style="margin-top: 15px;" @click="dialogFormVisible = true">
                                手动添加案例
                            </el-button>

                        </div>
                        <!-- <div class="loading" v-loading="caseLoading" element-loading-text="加载主题中……"
                            style="height: 60px;">
                        </div> -->
                        <div class="can-roll-left">
                            <!-- 弹出窗口 -->
                            <el-dialog v-model="dialogFormVisible" title="添加分析案例" width="500">
                                <el-form :model="form">
                                    <el-form-item label="情境标题" label-width="120px">
                                        <el-input v-model="form.title" placeholder="请输入情境标题" />
                                    </el-form-item>
                                    <el-form-item label="情境定义" label-width="120px">
                                        <el-input v-model="form.definition" autosize type="textarea"
                                            placeholder="请输入情境定义" />
                                    </el-form-item>
                                </el-form>
                                <template #footer>
                                    <div class="dialog-footer">
                                        <el-button @click="dialogFormVisible = false">取消</el-button>
                                        <el-button type="primary" @click="analyseOnceCaseWithText">确认</el-button>
                                    </div>
                                </template>
                            </el-dialog>
                            <!-- 改theme和GPT对话 -->

                            <div v-for="theme in analysedCaseSet" :key="theme.case" class="theme-card">
                                <el-card>
                                    <div class="card-title-header">
                                        <h2>{{ theme.case }}</h2>
                                        <div class="card-header">
                                            <el-button type="info" icon="EditPen" circle
                                                @click="toggleEdit(theme.case)" />
                                            <el-button type="warning" icon="Star" @click="starCase(theme)" circle />
                                            <el-button type="danger" icon="Delete" circle @click="deleteTheme(theme)" />
                                            <el-button type="primary" icon="ArrowRight"
                                                @click="analyseTextBySelectedCase(theme)" circle />
                                        </div>
                                    </div>

                                    <!-- 替换 el-descriptions 为 h3 标题和换行内容展示 -->
                                    <h3>代表课文</h3>
                                    <p>{{ theme.example_text_title }}</p>
                                    <p><strong>情境改编自相关话题：</strong><br />{{ theme.definition }}</p>

                                    <h3>描述</h3>
                                    <div v-if="expandedCase === theme.case">
                                        <el-input v-model="theme.detail" style="width: 100%;"
                                            :autosize="{ minRows: 2, maxRows: 10 }" type="textarea"
                                            placeholder="请输入描述内容" />
                                    </div>
                                    <div v-else>
                                        <p>{{ theme.detail }}</p>
                                    </div>

                                    <!-- 新增展开部分 -->
                                    <el-collapse v-if="expandedCase === theme.case">
                                        <el-divider>向AI提问</el-divider>

                                        <div v-for="(revision, index) in theme.revision" :key="index"
                                            class="history-item">
                                            <p><strong>User:</strong> {{ revision.request }}</p>
                                            <p style="margin-top: 8px;">AI: {{ revision.response }}</p>
                                            <el-divider v-if="index < theme.revision.length - 1" />
                                        </div>

                                        <el-divider />

                                        <el-input v-model="enteredAdvice" style="width: 100%; margin-top: 20px;"
                                            autosize type="textarea" placeholder="请输入你的建议" />

                                        <div style="margin-top: 20px;">
                                            <el-button type="primary"
                                                @click="submitAdvice(theme, enteredAdvice)">询问</el-button>
                                            <el-button type="success" @click="toggleEdit('')"
                                                style="margin-left: 10px;">保存并关闭窗口</el-button>
                                        </div>
                                    </el-collapse>
                                </el-card>
                            </div>
                            <div class="loading" v-loading="caseLoading" element-loading-text="加载主题中……"
                                style="height: 60px;">
                            </div>
                            <el-button type="primary" icon="Plus" style="margin-top: 15px;"
                                @click="moreAnalyseAndRankCases">更多主题……</el-button>
                        </div>
                    </div>

                </el-col>
                <el-col :span="8" class="exist-space">
                    <div class="card-title-header">
                        <h2> 和 {{ selectedCase }} 相关的课文……</h2>
                        <el-button type="primary" style="margin-top: 15px;"
                            @click="dialogVisible = true">添加重点关注的课文……</el-button>
                    </div>

                    <el-dialog v-model="dialogVisible" title="选择课文" width="500">
                        <p>双击选项可以浏览课文。</p>
                        <el-radio-group v-model="selectedText">
                            <el-radio v-for="text in textSet" :label="text" :key="text.title"
                                @dblclick="handleTitleClick(text.title)">
                                {{ text.title }}
                            </el-radio>
                        </el-radio-group>
                        <template #footer>
                            <div class="dialog-footer">
                                <el-button @click="dialogVisible = false">取消</el-button>
                                <el-button type="primary" @click="analyseText">确定</el-button>
                            </div>
                        </template>
                    </el-dialog>
                    <!-- TextEdit  EditText功能 -->

                    <div class="can-roll-mid">
                        <div v-for="(item, index) in analysedTextSet.ranked_text" :key="index" class="grid-content">
                            <el-card class="card" style="width: 100%; margin-bottom: 20px" shadow="always">
                                <div class="card-title-header">
                                    <h3 style="margin: 0;" @click="handleTitleClick(item.title)"
                                        class="clickable-title"><strong>{{
                item.title }}</strong></h3>
                                    <div class="card-header">
                                        <el-button type="info" icon="EditPen" circle
                                            @click="editTextBySelectedCase(item)" />
                                        <el-button type="warning" icon="Star" @click="starTextByCase(item)" circle />
                                        <el-button type="danger" icon="Delete" @click="deleteItem(index)" circle />
                                    </div>
                                </div>

                                <!-- 替换 el-descriptions 为 h3 标题和内容展示 -->
                                <!-- <h3>课文标题</h3>
                            <p><strong>{{ item.title }}</strong></p> -->

                                <h3>分析</h3>
                                <div v-if="textEditDialogVisible && selectedItem === item">
                                    <el-input v-model="item.analysed_text" style="width: 100%; margin-bottom: 20px;"
                                        :autosize="{ minRows: 2, maxRows: 10 }" type="textarea" placeholder="请输入分析内容" />
                                </div>
                                <div v-else>
                                    <p>{{ item.analysed_text }}</p>
                                </div>

                                <h3>AI给出的评分</h3>
                                <p>{{ item.rating }}</p>

                                <h3>理由</h3>
                                <p>{{ item.reason }}</p>

                                <div v-if="item.hovered" class="floating-button-container">
                                    <el-button type="primary" class="floating-button" @click="handleAddToRight(item)">
                                        添加到右边
                                    </el-button>
                                </div>

                                <div v-if="textEditDialogVisible && selectedItem === item" class="edit-section">
                                    <el-collapse v-if="selectedItem">
                                        <el-divider>向AI提问</el-divider>

                                        <div v-for="(revision, index) in selectedItem.revision" :key="index"
                                            class="history-item">
                                            <p><strong>User:</strong> {{ revision.request }}</p>
                                            <p style="margin-top: 8px;">AI: {{ revision.response }}</p>
                                            <el-divider v-if="index < selectedItem.revision.length - 1" />
                                        </div>

                                        <el-divider />

                                        <el-input v-model="enteredTextAdvice" style="width: 100%; margin-top: 20px;"
                                            autosize type="textarea" placeholder="请输入你的建议" />

                                        <div style="margin-top: 20px;">
                                            <el-button type="primary"
                                                @click="submitTextAdvice(selectedItem, enteredTextAdvice)">向AI提问</el-button>
                                            <el-button type="success" @click="textEditDialogVisible = false"
                                                style="margin-left: 10px;">关闭窗口</el-button>
                                        </div>
                                    </el-collapse>
                                </div>
                            </el-card>
                        </div>
                        <div class="loading" v-loading="textLoading" element-loading-text="分析课文中……"
                            style="height: 60px;">
                        </div>
                    </div>
                    <el-button type="primary" icon="Plus" style="margin-top: 15px;"
                        @click="analyseTextBySelectedCaseByselectedCaseObj">更多课文……</el-button>
                    <!-- <el-button type="plain" style="margin-top: 15px;">加载更多</el-button> -->
                </el-col>
                <el-col :span="6" class="exist-space">
                    <!-- 收藏夹 -->
                    <h2> 我的收藏夹 </h2>
                    <div class="demo-collapse">
                        <el-collapse v-model="activeNames">
                            <el-collapse-item v-for="(collection, index) in collectionsByCase" :key="index"
                                :title="collection.case.case" :name="collection.case.case">
                                <div>{{ collection.case.description }}</div>
                                <ul>
                                    <li v-for="(item, i) in collection.text" :key="i"
                                        @mouseenter="handleMouseEnter_i(i)" @mouseleave="handleMouseLeave_i(i)"
                                        :class="{ hovered: hoveredIndex === i }"
                                        @click="showCombinedDialog(collection)">
                                        <div class="item-content">
                                            <strong>{{ item.title }}</strong>
                                        </div>
                                        <div>{{ item.description }}</div>
                                    </li>
                                </ul>
                            </el-collapse-item>
                        </el-collapse>
                    </div>

                    <!-- Combined Dialog -->

                    <el-dialog v-model="caseDialogVisible" title="案例和课文详情" width="1500" :fullscreen="true"
                        :lock-scroll="true">
                        <!-- Case Details -->
                        <div class="summary-content" ref="summaryContent" @dblclick="toggleEditMode(false)">
                            <p>
                                <strong>情境：</strong>
                                <span v-if="!summaryEdit.case" @dblclick.stop="toggleEditMode(true, 'case')">{{
                selectedCaseInCollection.case.case
            }}</span>
                                <el-input v-else v-model="selectedCaseInCollection.case.case" type="textarea"
                                    :autosize="{ minRows: 2, maxRows: 15 }" placeholder="请输入情境"
                                    @blur="toggleEditMode(false)" />
                            </p>

                            <p>
                                <strong>定义：</strong>
                                <span v-if="!summaryEdit.definition"
                                    @dblclick.stop="toggleEditMode(true, 'definition')">{{
                selectedCaseInCollection.case.definition
            }}</span>
                                <el-input v-else v-model="selectedCaseInCollection.case.definition" type="textarea"
                                    :autosize="{ minRows: 2, maxRows: 15 }" placeholder="请输入定义"
                                    @blur="toggleEditMode(false)" />
                            </p>

                            <p>
                                <strong>分析：</strong>
                                <span v-if="!summaryEdit.detail" @dblclick.stop="toggleEditMode(true, 'detail')">{{
                selectedCaseInCollection.case.detail
            }}</span>
                                <el-input v-else v-model="selectedCaseInCollection.case.detail" type="textarea"
                                    :autosize="{ minRows: 2, maxRows: 15 }" placeholder="请输入分析"
                                    @blur="toggleEditMode(false)" />
                            </p>

                            <!-- Text List -->
                            <ul>
                                <li v-for="(text, index) in selectedCaseInCollection.text" :key="index">
                                    <el-tag type="primary">课文 {{ index + 1 }}</el-tag>
                                    <h3>
                                        <span v-if="!summaryEdit['title' + index]"
                                            @dblclick.stop="toggleEditMode(true, 'title' + index)">{{ text.title
                                            }}</span>
                                        <el-input v-else v-model="text.title" type="textarea"
                                            :autosize="{ minRows: 2, maxRows: 15 }" placeholder="请输入标题"
                                            @blur="toggleEditMode(false)" />
                                    </h3>
                                    <p>
                                        <strong>分析：<br /></strong>
                                        <span v-if="!summaryEdit['analysed_text' + index]"
                                            @dblclick.stop="toggleEditMode(true, 'analysed_text' + index)">
                                            {{ text.analysed_text }}
                                        </span>
                                        <el-input v-else v-model="text.analysed_text" type="textarea"
                                            :autosize="{ minRows: 2, maxRows: 15 }" placeholder="请输入分析内容"
                                            @blur="toggleEditMode(false)" />
                                    </p>
                                    <el-divider></el-divider>
                                </li>
                            </ul>

                            <!-- Plan and Intro -->
                            <el-row>
                                <el-col :span="13">
                                    <div v-if="selectedCaseInCollection.summary.plan !== ''">
                                        <div>
                                            <h2>课时安排</h2>
                                            <span v-if="!summaryEdit.coursePlan"
                                                @dblclick.stop="toggleEditMode(true, 'coursePlan')">{{
                selectedCaseInCollection.summary.plan }}</span>
                                            <el-input v-else v-model="selectedCaseInCollection.summary.plan"
                                                type="textarea" :autosize="{ minRows: 2, maxRows: 15 }"
                                                placeholder="请输入课时安排" @blur="toggleEditMode(false)" />
                                        </div>
                                        <div><el-button type="success" @click="generateActivities"
                                                style="margin-top: 20px;">生成活动</el-button>
                                        </div>
                                    </div>
                                </el-col>
                                <el-col :span="2">
                                    <el-divider direction="vertical" border-stle="dashed" />
                                </el-col>
                                <el-col :span="9">
                                    <div v-if="selectedCaseInCollection.summary.intro">
                                        <h2>引言</h2>
                                        <span v-if="!summaryEdit.courseIntro"
                                            @dblclick.stop="toggleEditMode(true, 'courseIntro')">
                                            {{ selectedCaseInCollection.summary.intro }}
                                        </span>
                                        <el-input v-else v-model="selectedCaseInCollection.summary.intro"
                                            type="textarea" :autosize="{ minRows: 2, maxRows: 15 }" placeholder="请输入引言"
                                            @blur="toggleEditMode(false)" />
                                    </div>
                                </el-col>
                                <!-- Display Activities -->
                                <div v-if="selectedCaseInCollection.summary.activities.length > 0">
                                    <h2>活动列表</h2>
                                    <ul>
                                        <li v-for="(activity, index) in selectedCaseInCollection.summary.activities"
                                            :key="index">
                                            <div v-for="(line, lineIndex) in activity.split('\n\n')" :key="lineIndex">
                                                <span @click="confirmDeleteActivity(index, lineIndex)"
                                                    @mouseover="hoverMessage = '单击删除'" @mouseleave="hoverMessage = ''"
                                                    style="color: #87CEFA; font-weight: bold; cursor: pointer;">
                                                    {{ line.trim().split(' ')[0] }}
                                                </span>
                                                <span>
                                                    {{ line.trim().substring(line.trim().indexOf(' ')) }}
                                                </span>
                                            </div>
                                        </li>
                                    </ul>
                                    <!-- <div v-if="hoverMessage" style="color: #999; margin-top: 10px;">
                                        {{ hoverMessage }}
                                    </div> -->
                                </div>
                            </el-row>
                            <div class="loading" v-loading="summaryLoading" element-loading-text="规划课程中……"
                                style="height: 60px;">
                            </div>
                        </div>

                        <!-- Footer Buttons -->
                        <template #footer>
                            预计课时数:<el-input v-model="classNum" placeholder="请填写预计课时数"
                                style="width: 200px; margin-right: 10px;"></el-input>
                            <el-button type="primary" @click="generateCoursePlan"
                                v-if="selectedCaseInCollection.summary.intro === ''">生成课程安排和引言</el-button>
                            <el-button type="warning" @click="generateCoursePlan"
                                v-if="selectedCaseInCollection.summary.intro !== ''">重新生成</el-button>
                            <el-button type="success" @click="downloadHtml"
                                v-if="selectedCaseInCollection.summary.intro !== ''">下载 HTML</el-button>
                            <el-button type="success" @click="downloadTxt"
                                v-if="selectedCaseInCollection.summary.intro !== ''">下载 TXT</el-button>
                            <el-button @click="caseDialogVisible = false" style="margin-left: 10px;">关闭</el-button>
                        </template>
                    </el-dialog>
                </el-col>
            </el-row>
        </div>

    </div>
</template>

<script>
import axios from 'axios'
import { ElMessageBox, ElMessage } from 'element-plus'
export default {
    data() {
        return {
            courseName: '',
            courseContent: '',
            courseLevel: '',
            isConfigOpen: true,
            subjects: ['数学', '科学', '综合实践', '美术', '音乐'],  // Dynamically generated checkboxes
            caseSet: [],
            textSet: [],
            selectedItem: null,
            selectedSubjects: [],
            textTitles: [],
            caseCounter: 0,
            textCounter: 0,
            expandedCase: '', // 用于记录当前展开的 case
            loadingCase: false,
            loadingCase: false,
            hoveredIndex: -1, // 当前悬浮的项目索引
            textList: [],
            textEditDialogVisible: false,
            dialogFormVisible: false, // 添加case
            dialogVisible: false,
            editTextdialogVisible: false,
            form: {
                title: '',
                definition: '',
            }, // 添加case
            enteredAdvice: '',
            enteredTextAdvice: '',
            selectedText: null,
            selectedCase: '',
            analysedTextSet: { "ranked_text": [] },
            analysedCaseSet: [],
            collectionsByCase: [],
            coursePlan: '', // 用于存储生成的计划
            courseIntro: '', // 用于存储生成的引言
            items: [
                {
                    title: '故宫',
                    subject: '地理',
                    description: '课文充满了历史气息，漫步在历史的大道上，我们会有怎样的遐想……',
                    related: '自幼就见过“天苍苍，野茫茫，风吹草低见牛羊”这类的词句。这曾经发生过不太好的影响，使人怕到北边去。',
                    selectedTexts: [],
                    hovered: false,
                },
                {
                    title: '草原',
                    subject: '计算机科学',
                    description: '从城市到草原，也有不一样的魅力。',
                    related: '自幼就见过“天苍苍，野茫茫，风吹草低见牛羊”这类的词句。这曾经发生过不太好的影响，使人怕到北边去。',
                    selectedTexts: [],
                    hovered: false,
                },
            ],
            collections: [],
            activeNames: [], // 默认所有面板打开
            caseDialogVisible: false,
            selectedCaseInCollection: {}, // 存储选中的Case及其相关内容
            classNum: 6,
            counterPlus: 6,
            selectedCaseObj: null,
            caseLoading: false,
            textLoading: false,
            summaryLoading: false,
            summaryEdit: {
                case: false,
                definition: false,
                detail: false,
                coursePlan: false,
                courseIntro: false,
            },
            hoverMessage: '', // 用于显示悬浮提示信息
        };
    },
    created() {
        this.fetchTextList();
    },
    methods: {
        async fetchTextList() {
            try {
                const response = await axios.get('/explore/get-text-title-list');
                this.textList = response.data.map((item, index) => {
                    // 判断 type 是否为 '语文园地', '写作', 或 '口语交际'
                    const typesToAppend = ['语文园地', '写作', '口语交际'];

                    // 如果满足条件，则在 label 后面加上 type 名
                    const label = typesToAppend.includes(item.type) ? `${item.title} (${item.type})` : item.title;

                    return {
                        key: index + 1, // 从1开始编号
                        label: label,
                        type: item.type,
                        disabled: false
                    };
                });
            } catch (error) {
                console.error('Error fetching text list:', error);
            }
        },
        async getCases() {
            try {
                // 获取当前选中的学科
                // const selectedSubject = this.selectedSubjects[0];

                // 判断是否为指定科目
                // if (['科学', '数学', '美术', '音乐'].includes(selectedSubject)) {
                //     this.caseSet = [{ "process": selectedSubject, "embedding": [] }];
                //     console.log('Special case, setting caseSet directly:', this.caseSet);
                //     return;
                // }

                const selectedSubjects = { "subjects": this.selectedSubjects };
                // 发送POST请求
                const response = await axios.post('/explore/get-cases-by-categories', selectedSubjects);

                // 检查响应是否成功
                if (response.status === 200) {
                    const cases = response.data;
                    // 将返回的结果存入本地存储
                    this.caseSet = cases;
                    localStorage.setItem('cases', JSON.stringify(cases));

                    console.log('Cases data saved to localStorage:', cases);
                } else {
                    console.error('Failed to fetch cases:', response.status);
                }
            } catch (error) {
                console.error('Error fetching cases:', error);
            }
        },
        async getTextSet() {
            try {
                // 从 textList 中根据 textTitles 获取对应的标题列表
                const selectedTitles = this.textList
                    .filter(item => this.textTitles.includes(item.key))
                    .map(item => item.label);

                // 构建请求体
                const requestData = {
                    titles: selectedTitles
                };

                // 发送请求到 /explore/get-texts-by-titles 接口
                const response = await axios.post('/explore/get-texts-by-titles', requestData);
                // 检查响应是否成功
                if (response.status === 200) {
                    const textSet = response.data;
                    // 将结果存入 textSet
                    this.textSet = textSet;
                    // 将结果存入 localStorage
                    localStorage.setItem('textSet', JSON.stringify(textSet));
                    console.log('Text data saved to localStorage:', textSet);
                } else {
                    console.error('Failed to fetch texts:', response.status);
                }
            } catch (error) {
                console.error('Error fetching texts:', error);
            }
        },

        async analyseAndRankCases() {
            try {
                // 重置状态变量
                this.analysedCaseSet = [];
                this.loadingCase = true;
                this.caseLoading = true;
                this.caseCounter = 0;

                // 获取 cases 和 textSet
                await this.getCases();
                await this.getTextSet();

                // 确保 textSet 和 caseSet 都已经获取到
                while (!this.textSet || !this.caseSet || this.textSet.length === 0 || this.caseSet.length === 0) {
                    await new Promise(resolve => setTimeout(resolve, 100)); // 每100ms检查一次
                }

                // 发送分析和排名请求
                const response = await axios.post('/explore/analyse-and-rank-cases-with-text', {
                    texts: this.textSet,
                    cases: this.caseSet,
                    counter: this.caseCounter // 传递当前的计数器值
                });

                const results = response.data.analysed_case_set;

                const newResults = results
                    .filter(result => result.format === true)
                    .map(result => ({
                        case: result.case,
                        example_text_title: result.example_text_title,
                        detail: result.detail,
                        definition: result.definition,
                        origin: result.origin,
                        embedding: result.embedding,
                        revision: []
                    }));

                // 将新的结果插入到analysedCaseSet的开头
                this.analysedCaseSet = [...this.analysedCaseSet, ...newResults];

                console.log('Filtered and mapped results:', this.analysedCaseSet);
                this.caseCounter += this.counterPlus;

            } catch (error) {
                console.error('Error during analysis:', error);
            } finally {
                // 确保在任何情况下都重置 loading 状态
                this.loadingCase = false;
                this.caseLoading = false;
            }
        },
        async moreAnalyseAndRankCases() {
            try {
                this.caseLoading = true;
                const response = await axios.post('/explore/analyse-and-rank-cases-with-text', {
                    texts: this.textSet,
                    cases: this.caseSet,
                    counter: this.caseCounter // 传递当前的计数器值
                });

                const results = response.data.analysed_case_set;
                console.log(results);

                const newResults = results
                    .filter(result => result.format === true)
                    .map(result => ({
                        case: result.case,
                        example_text_title: result.example_text_title,
                        detail: result.detail,
                        definition: result.definition,
                        origin: result.origin,
                        embedding: result.embedding,
                        revision: []
                    }));

                // 将新的结果插入到analysedCaseSet的开头
                this.analysedCaseSet = [...this.analysedCaseSet, ...newResults];

                console.log('Filtered and mapped results:', this.analysedCaseSet);
                this.loadingCase = false;
                this.caseCounter += this.counterPlus;
                this.caseLoading = false;
            } catch (error) {
                this.loadingCase = false;
                this.caseLoading = false;
                console.error('Error during analysis:', error);
            }
        },
        deleteTheme(theme) {
            this.$confirm('此操作将永久删除该案例, 是否继续?', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            }).then(() => {
                const index = this.analysedCaseSet.indexOf(theme);
                if (index > -1) {
                    this.analysedCaseSet.splice(index, 1);
                }
                this.$message({
                    type: 'success',
                    message: '删除成功!'
                });
            }).catch(() => {
                this.$message({
                    type: 'info',
                    message: '已取消删除'
                });
            });
        },
        async analyseTextBySelectedCase(theme) {
            try {
                this.textLoading = true;
                this.textCounter = 0;
                this.selectedCaseObj = theme;
                this.selectedCase = theme.case;
                // 清空AnalysedTextSet
                this.analysedTextSet = { "ranked_text": [] };
                const response = await axios.post('/explore/analyse-text-by-selected-case', {
                    selected_case: theme,
                    texts: this.textSet,
                    counter: this.textCounter
                });

                if (response.status === 200) {
                    // console.log(response.data)
                    this.analysedTextSet.ranked_text = [...this.analysedTextSet.ranked_text, ...response.data.ranked_text];
                    this.textCounter += this.counterPlus;
                    this.textLoading = false;
                } else {
                    console.error('请求失败，状态码:', response.status);
                    this.textLoading = false;
                }
            } catch (error) {
                console.error('请求出错:', error);
                this.textLoading = false;
            }
        },
        async analyseTextBySelectedCaseByselectedCaseObj() {
            try {
                // 判断是否已经分析完所有课文
                if (this.textCounter >= this.textSet.length) {
                    ElMessage({
                        message: '所有课文已经被分析！',
                        type: 'warning',
                    });
                    return; // 阻止后续代码的执行
                }

                this.textLoading = true;
                const theme = this.selectedCaseObj;
                this.selectedCase = theme.case;
                const response = await axios.post('/explore/analyse-text-by-selected-case', {
                    selected_case: theme,
                    texts: this.textSet,
                    counter: this.textCounter
                });

                if (response.status === 200) {
                    // 更新 analysedTextSet 和 textCounter
                    this.analysedTextSet.ranked_text = [...this.analysedTextSet.ranked_text, ...response.data.ranked_text];
                    this.textCounter += this.counterPlus;
                    this.textLoading = false;
                } else {
                    console.error('请求失败，状态码:', response.status);
                    this.textLoading = false;
                }
            } catch (error) {
                console.error('请求出错:', error);
                this.textLoading = false;
            }
        },
        // 这里是caseEdit
        toggleEdit(caseName) {
            this.expandedCase = this.expandedCase === caseName ? '' : caseName;
        },
        async submitAdvice(theme, enteredAdvice) {
            try {
                const response = await axios.post('/explore/edit-one-case-with-text', {
                    selected_case: theme,
                    texts: this.textSet,
                    advice: enteredAdvice,
                });
                // 将服务器响应内容加入到历史记录中
                theme.revision.push({
                    request: enteredAdvice,
                    response: response.data.response
                });
                this.enteredAdvice = ''; // 清空输入框内容
            } catch (error) {
                console.error('提交建议时发生错误:', error);
            }
        },
        starCase(caseItem) {
            // 检查该 case 是否已经在收藏夹中
            const existingCase = this.collectionsByCase.find(
                collection => collection.case.case === caseItem.case
            );

            // 如果不存在则添加到 collectionsByCase 中
            if (!existingCase) {
                this.collectionsByCase.push({
                    case: caseItem,
                    text: [],
                    summary: { plan: "", intro: "", activities: [] }
                });
            }
        },
        starTextByCase(text) {
            // 在 this.analysedCaseSet 中找到一个 item
            const item = this.analysedCaseSet.find(
                analysedItem => analysedItem.case === this.selectedCase
            );

            // 将找到的 item 传递给 starCase
            if (item) {
                this.starCase(item);
            }

            // 找到当前选中的 case
            const selectedCase = this.collectionsByCase.find(
                collection => collection.case.case === this.selectedCase
            );

            if (selectedCase) {
                // 检查 text 是否已经在该 case 下存在
                const existingText = selectedCase.text.find(t => t.title === text.title);

                // 如果不存在则添加到该 case 的 text 列表中
                if (!existingText) {
                    selectedCase.text.push(text);
                }
            }
        },
        async analyseOnceCaseWithText() {
            try {
                this.caseLoading = true;
                // 使用 Axios 发送请求
                const response = await axios.post('/explore/analyse-one-case-with-text', {
                    texts: this.textSet,
                    cases: [{
                        process: `${this.form.title}: ${this.form.definition}`,
                        embedding: [],
                    }],
                    counter: 0,
                });
                // 获取返回的分析结果
                const analysedCase = response.data.analysed_case;

                // 添加 revision: [] 属性
                analysedCase.revision = [];

                // 将结果放入 analysedCaseSet 的开头
                this.analysedCaseSet.unshift(analysedCase);

                // 关闭弹窗
                this.dialogFormVisible = false;
                // 清空输入框
                this.form.title = '';
                this.form.definition = '';
                this.caseLoading = false;
            } catch (error) {
                console.error('分析失败：', error);
                this.caseLoading = false;
            }
        },
        analyseText() {
            const selectedCaseObj = this.analysedCaseSet.find(
                (caseObj) => caseObj.case === this.selectedCase
            );

            if (!selectedCaseObj || !this.selectedText) {
                this.$message.error("请先选择课文");
                return;
            }

            axios.post('/explore/analyse-one-text-by-selected-case', {
                selected_case: selectedCaseObj,
                texts: [this.selectedText],
                counter: 0
            }).then(response => {
                // 假设response.data返回的是分析结果
                console.log(response.data.ranked_text)
                this.analysedTextSet.ranked_text.unshift(response.data.analysed_text);
                this.dialogVisible = false;
            }).catch(error => {
                console.error(error);
                this.dialogVisible = false;
                this.$message.error("分析失败，请重试");
            });
        },
        editTextBySelectedCase(item) {
            this.selectedItem = item;
            this.textEditDialogVisible = !this.textEditDialogVisible;
        },
        submitTextAdvice(item, advice) {
            const selectedText = this.textSet.find(
                (text) => text.title === item.title
            );

            const selectedCaseObj = this.analysedCaseSet.find(
                (caseObj) => caseObj.case === this.selectedCase
            );

            if (!selectedText || !selectedCaseObj || !advice) {
                this.$message.error("请确保所有输入项都已填写完整");
                return;
            }

            axios.post('/explore/edit-one-text-by-selected-case', {
                selected_case: selectedCaseObj,
                texts: [selectedText],
                advice: advice
            }).then(response => {
                item.revision.push({
                    request: advice,
                    response: response.data.revision
                });
                this.enteredTextAdvice = ''; // 清空输入框内容
                this.editTextdialogVisible = false;
            }).catch(error => {
                console.error(error);
                this.$message.error("修改失败，请重试");
            });
        },
        submitCourse() {
            console.log('Course submitted:', this.courseName, this.courseContent, this.courseLevel);
            // 这里添加提交课程的逻辑
        },
        confirmSelection() {
            console.log('Selected Articles:', this.selectedArticles);
            // Further logic can be implemented as needed
        },
        handleSubjectClick(subject) {
            this.$message({
                message: `点击显示全文内容……`,
                type: 'info',
            })
        },
        handleAddToRight(item) {
            this.$message({
                message: `将 ${item.title} 添加到右边`,
                type: 'success',
            })
        },
        // handleMouseEnter(index) {
        //     this.items[index].hovered = true
        // },
        // handleMouseLeave() {
        //     this.items.forEach((item) => {
        //         item.hovered = false
        //     })
        // },
        addCollection(item) {
            // Check if the item is already in the collections
            const exists = this.collections.find((c) => c.title === item.title)
            if (!exists) {
                this.collections.push({ ...item, hovered: false })
                this.$message({
                    message: `${item.title} 已添加到收藏夹`,
                    type: 'success',
                })
            } else {
                this.$message({
                    message: `${item.title} 已在收藏夹中`,
                    type: 'warning',
                })
            }
        },
        // handleMouseEnter(index) {
        //     this.collections[index].hovered = true
        // },
        // handleMouseLeave() {
        //     this.collections.forEach((item) => {
        //         item.hovered = false
        //     })
        // },
        handleDelete(index) {
            const selectedCase = this.collectionsByCase.find(
                collection => collection.case.case === this.selectedCase
            );
            if (selectedCase) {
                selectedCase.text.splice(index, 1);
            }
        },
        showDetails(collection) {
            // Show details logic here
            this.$message({
                message: `显示 ${collection.title} 的详细信息`,
                type: 'info',
            })
        },
        handleMouseEnter_i(index) {
            this.hoveredIndex = index;
        },
        handleMouseLeave_i(index) {
            if (this.hoveredIndex === index) {
                this.hoveredIndex = null;
            }
        },
        handleDelete(index) {
            this.items.splice(index, 1);
        },
        showCombinedDialog(collection) {
            this.courseIntro = '';
            this.coursePlan = '';
            this.selectedCaseInCollection = collection;
            this.caseDialogVisible = true;
        },
        generateCoursePlan() {
            this.summaryLoading = true;
            this.selectedCaseInCollection.summary.activities = [];
            axios.post('/explore/plan-course', {
                case: this.selectedCaseInCollection.case,
                text: this.selectedCaseInCollection.text,
                class_num: this.classNum
            }).then(response => {
                this.coursePlan = response.data.plan;
                this.courseIntro = response.data.intro;

                // 将生成的计划和引言存入到 selectedCaseInCollection 的 summary 中
                this.selectedCaseInCollection.summary.plan = this.coursePlan;
                this.selectedCaseInCollection.summary.intro = this.courseIntro;

                this.summaryLoading = false;
            }).catch(error => {
                console.error(error);
                this.$message.error("生成课程安排和引言失败，请重试");
                this.summaryLoading = false;
            });
        },
        deleteItem(index) {
            this.$confirm('此操作将永久删除该项, 是否继续?', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            }).then(() => {
                this.analysedTextSet.ranked_text.splice(index, 1);
                this.$message({
                    type: 'success',
                    message: '删除成功!'
                });
            }).catch(() => {
                this.$message({
                    type: 'info',
                    message: '已取消删除'
                });
            });
        },
        async handleTitleClick(title) {
            try {
                const response = await axios.post('/explore/get-text-by-title', { title })

                if (response.data && response.data.text) {
                    const formattedText = response.data.text.replace(/\n/g, '<br>') // 替换换行符为 <br>
                    ElMessageBox.alert(formattedText, title, {
                        dangerouslyUseHTMLString: true, // 使用 HTML 字符串
                        confirmButtonText: '关闭',
                        // callback: (action) => {
                        // ElMessage({
                        //     type: 'info',
                        //     message: `显示课文成功`,
                        // })
                        // },
                    })
                } else {
                    ElMessage({
                        type: 'error',
                        message: '未找到对应的课文内容',
                    })
                }
            } catch (error) {
                ElMessage({
                    type: 'error',
                    message: '获取课文内容失败',
                })
            }
        },
        downloadTxt() {
            // 获取对话框中的纯文本内容
            const summaryElement = this.$refs.summaryContent;
            const textContent = summaryElement.innerText;

            // 创建一个 blob 对象
            const blob = new Blob([textContent], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);

            // 创建下载链接并触发下载
            const a = document.createElement('a');
            a.href = url;
            a.download = 'summary.txt';
            a.click();
            URL.revokeObjectURL(url);
        },

        downloadHtml() {
            // 获取对话框中的 HTML 内容
            const summaryElement = this.$refs.summaryContent;
            const htmlContent = summaryElement.outerHTML;

            // 创建一个 blob 对象
            const blob = new Blob([htmlContent], { type: 'text/html' });
            const url = URL.createObjectURL(blob);

            // 创建下载链接并触发下载
            const a = document.createElement('a');
            a.href = url;
            a.download = 'summary.html';
            a.click();
            URL.revokeObjectURL(url);
        },
        toggleEditMode(enable, field = null) {
            if (field) {
                this.summaryEdit[field] = enable;
            } else {
                // 如果双击了 dialog 的 padding 区域，关闭所有编辑模式
                Object.keys(this.summaryEdit).forEach((key) => {
                    this.summaryEdit[key] = false;
                });
            }
        },
        generateActivities() {
            this.summaryLoading = true;
            axios.post('/explore/plan-activities', {
                case: this.selectedCaseInCollection.case,
                text: this.selectedCaseInCollection.text,
                summary: this.selectedCaseInCollection.summary
            }).then(response => {
                const activity = response.data.activities; // 假设返回的是一个字符串
                this.selectedCaseInCollection.summary.activities.push(activity); // 将活动添加到activities中
                this.summaryLoading = false;
            }).catch(error => {
                console.error(error);
                this.$message.error("生成活动失败，请重试");
                this.summaryLoading = false;
            });
        },
        getFirstWord(activity) {
            return activity.split(' ')[0];
        },
        getActivityDescription(activity) {
            return activity.substring(activity.indexOf(' '));
        },
        confirmDeleteActivity(activityIndex, lineIndex) {
            this.$confirm('确定要删除这个活动吗？', '确认删除', {
                confirmButtonText: '删除',
                cancelButtonText: '取消',
                type: 'warning',
            }).then(() => {
                this.deleteActivityLine(activityIndex, lineIndex);
            }).catch(() => {
                // 用户取消删除，无需执行操作
            });
        },
        deleteActivityLine(activityIndex, lineIndex) {
            this.selectedCaseInCollection.summary.activities[activityIndex] = this.selectedCaseInCollection.summary.activities[activityIndex]
                .split('\n\n')
                .filter((line, idx) => idx !== lineIndex)
                .join('\n\n');

            // 移除空活动
            if (!this.selectedCaseInCollection.summary.activities[activityIndex].trim()) {
                this.selectedCaseInCollection.summary.activities.splice(activityIndex, 1);
            }
        }
    }
};
</script>

<style scoped>
header {
    display: flex;
    align-items: center;
    padding: 0 10%;
    border-bottom: 1px solid rgb(234, 230, 230);
}

header ul {
    margin-left: auto;
}

header li {
    list-style: none;
    display: inline-block;
    margin-right: 20px;
    font-size: 14px;
    color: rgb(118, 112, 112);
    cursor: pointer;
}

header li#selected {
    border-bottom: 2px solid rgb(15, 212, 143);
    padding-bottom: 4px;
}

.nav {
    padding: 20px 170px;
    border: 1px solid rgb(234, 230, 230);
}

.mainx {
    width: 95%;
    margin: 0 auto;
    padding: 40px 0;
}

.el-input,
.el-button {
    margin-bottom: 20px;
}

.bordered-checkboxes .el-checkbox {
    margin-right: 10px;
}

hr {
    margin-top: 20px;
    margin-bottom: 20px;
}

.section {
    margin-bottom: 20px;
}

.theme-card {
    margin-bottom: 10px;
}

.empty-message {
    text-align: center;
    color: #999;
    margin: 20px 0;
}

.collection-card {
    position: relative;
    margin-bottom: 10px;
    cursor: pointer;
    transition: all 0.3s ease;
}

.details-button {
    position: absolute;
    bottom: 10px;
    right: 10px;
    transition: opacity 0.3s;
}

.card-title-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.card-header {
    display: flex;
    gap: 10px;
}

.card-header-text {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    /* Optional: Adds space between buttons */
}

.demo-collapse {
    margin: 20px;
}

.hovered {
    background-color: #f0f0f0;
}

li {
    padding: 10px;
    transition: background-color 0.3s;
}

li.hovered {
    background-color: #f5f5f5;
}

.item-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.item-content strong {
    flex: 1;
}

.dialog-footer {
    text-align: right;
}

.box-card {
    margin-bottom: 20px;
}

.exist-space {
    white-space: pre-wrap;
}

.loading {
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.config-button {
    margin-left: auto;
}

.config-button-container {
    display: flex;
    align-items: center;
    /* 如果需要垂直居中 */
}

.can-roll-left {
    max-height: 700px;
    /* 固定高度，您可以根据需要调整 */
    overflow-y: auto;
    /* 垂直方向开启滚动条 */
    padding: 18px;
    /* 给内容一些内边距，以防滚动条遮挡内容 */
    border: 1px solid #ebebeb;
    /* 可选：给区域添加边框以区分其他内容 */
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    /* 可选：添加阴影效果 */
}

.can-roll-mid {
    max-height: 750px;
    /* 固定高度，您可以根据需要调整 */
    overflow-y: auto;
    /* 垂直方向开启滚动条 */
    padding: 18px;
    /* 给内容一些内边距，以防滚动条遮挡内容 */
    border: 1px solid #ebebeb;
    /* 可选：给区域添加边框以区分其他内容 */
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    /* 可选：添加阴影效果 */
}

.clickable-title {
    cursor: pointer;
    color: black;
    transition: color 0.3s;
}

.clickable-title:hover {
    color: #1e90ff;
    /* 浅蓝色 */
}

.summary-content {
    padding-right: 15%;
    padding-left: 15%;
    /* 内容内边距，增加两侧间隔 */
    font-size: 18px;
    /* 字体大小稍大 */
    color: #000;
    /* 纯黑色字体 */
    line-height: 1.6;
    /* 行距，增加可读性 */
}

.summary-content h3 {
    font-size: 24px;
    /* 标题稍大一些 */
    margin-top: 15px;
    margin-bottom: 10px;
    color: #000;
}

.summary-content p {
    margin: 10px 0;
    /* 上下间隔，使段落更分明 */
}

.summary-content strong {
    font-weight: bold;
    /* 加粗强调的文本 */
}

.summary-content ul {
    list-style-type: none;
    /* 去掉列表符号 */
    padding: 0;
    margin: 0;
}

.summary-content ul li {
    margin-bottom: 20px;
    /* 列表项之间增加间隔 */
}

.summary-content .el-divider {
    margin: 20px 0;
    /* 增加分隔符的上下间距 */
}
</style>
