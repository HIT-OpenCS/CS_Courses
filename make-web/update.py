import requests
import termcolor
import logging
import os
import yaml
import shutil
from pprint import pprint
from custom_logger import setup_logger

# =============== 可供选择: DEBUG INFO WARNING ERROR CRITICAL =============== 
logger = setup_logger(__name__, loglevel='DEBUG')


def colored_print(param, color: str):
    print(termcolor.colored(param, color))


class WebsiteUpdater:
    def __init__(self, path: str):
        
        self.registered_majors = ['公共课程', '计算机科学与技术', '人工智能', '物联网工程', '软件工程', '数据科学与大数据技术', '网络空间安全', '信息安全', '选修课程']
        
        # 支持的readme格式
        self.readme_name = ['README.md', '课程说明.md']
        
        # 支持的资源后缀名
        self.resource_suffix = ['pdf', 'ppt', 'pptx', 'doc', 'docs']
        
        self.base_path = path
        self.url_prefix = "https://raw.githubusercontent.com/HIT-FC-OpenCS/CS_Courses/main"
        
        self.resource_dict = {}   # 使用相对路径存储
        
        self.root_dir_name = self.base_path.split('\\')[-1]  # 一般root_dir_name为CS_Course，除非本地乱改了名字
        
        
    def get_resource(self):
        """   
        初始化self.resource_dict
        resource_dict 组织形式示例 (此处的path均为相对于CS_Courses的相对路径):
        {
            '计算机科学与技术': {
                '计算机体系结构: {
                    'readme_path': <path>, 
                    'resource_path': [<path>, <path>]
                },
                '计算理论': {
                    'readme_path': <path>, 
                    'resource_path': [<path>, <path>]
                }
            },
            '人工智能': {
                '模式识别与机器学习': {
                    'readme_path': <path>, 
                    'resource_path': [<path>, <path>]
                }
            }
        }
        """
        # =============== 遍历专业 =============== 
        for major in os.listdir(self.base_path):
            if major in self.registered_majors:
                
                self.resource_dict[major] = {}
                # =============== 遍历专业下开设的课程 =============== 
                for course in os.listdir(os.path.join(self.base_path, major)):
                    
                    self.resource_dict[major][course] = {
                        'readme_path': None,
                        'resource_path': []
                    }
                    if os.path.isdir(os.path.join(self.base_path, major, course)):
                        for item in os.listdir(os.path.join(self.base_path, major, course)):
                            current_abs_path = os.path.join(self.base_path, major, course, item)
                            # 如: 课程复习资料、课程练习题目、README.md
                            if item in self.readme_name:
                                # =============== 识别出readme文件 =============== 
                                
                                logger.debug('Found readme file. Relative path: {}'.format(os.path.relpath(current_abs_path, self.base_path)))
                                self.resource_dict[major][course]['readme_path'] = os.path.relpath(current_abs_path, self.base_path)
                            
                            elif os.path.isdir(current_abs_path):
                                for resource in os.listdir(current_abs_path):

                                    if resource.split('.')[-1] in self.resource_suffix:
                                        # =============== 识别出资源文件 =============== 
                                        logger.debug('Found resource file: {}'.format(resource))
                                        self.resource_dict[major][course]['resource_path'].append(os.path.relpath(os.path.join(current_abs_path, resource), self.base_path))
                        
            
        if len(self.resource_dict) == 0:
            logger.error('The resource dict is empty, which is unusual. Please check the file storage path and try the script again.')
            exit(1)

        logger.info('Successfully initialized resource dict.')
        # pprint(self.resource_dict)
        
    
    def write_single_md(self, course_name: str, md_path: str or None, resource_path_list: list, target_dir: str, strict_mode: bool = False):
        """  
        自动生成markdown文件，注意这会覆盖掉之前的md文件
        默认生成的md文件名称为<课程名称>.md
        需要提供绝对路径
        """
        final_text = []
        if md_path is not None:
            with open(md_path, 'r', encoding='utf-8') as raw_file:
                final_text = raw_file.readlines()
                final_text.append('\n\n### 资源列表\n\n')  
            raw_file.close()  
                        
        else:
            final_text = ['## {}\n\n### 资源列表\n\n'.format(course_name)]
        
        # =============== 根据resource_path_list，构造相应的url，填入到final_text中   
        for resource_path in resource_path_list:
            resource_url = self.url_prefix + resource_path.split('CS_Courses')[-1]
            resource_url = resource_url.replace('\\', '/')
            logger.debug('url: {}'.format(resource_url))
            
            file_name = resource_url.split('/')[-1].split('.')[0]
            logger.debug('file name: {}'.format(file_name))
            
            # 若开启strict_mode，则会先通过requests库尝试访问url链接，若成功响应再填入该链接
            if strict_mode:
                resp = requests.get(resource_url)
                logger.debug('status code: {}'.format(resp.status_code))
                if resp.status_code == 200:
                    final_text.append('- [{}]({})\n'.format(file_name, resource_url))
            
            # 不开启strict_mode，直接填url
            else:
                final_text.append('- [{}]({})\n'.format(file_name, resource_url))

        if len(final_text) == 0:
            logger.error('Something went wrong when processing final text. The final text is empty.')
            exit(1)
        
        # =============== 根据final_text，写入markdown文件中，文件名为<课程名称>.md =============== 
        target_file_path = os.path.join(target_dir, '{}.md'.format(course_name))
        with open(target_file_path, 'w', encoding='utf-8') as md_file:
            md_file.writelines(final_text)
        md_file.close()  
        logger.debug('write md file: {}'.format(target_file_path))
    
    
    def update_docs(self):
        """ 
        修改docs文件夹下的内容
        """     
        if len(self.resource_dict) == 0:
            logging.ERROR("The current resource dict is empty. Please run function 'get_resource' first.")
            exit(1)
        
        docs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'docs')
        # colored_print(docs_path, 'yellow')
        
        # =============== 更新各个专业/课程下的md文件 =============== 
        for major in self.resource_dict.keys():
            # 绝对路径
            major_path = os.path.join(docs_path, major)
            
            # 若文件夹已存在，则会先删除该文件夹，之后重新生成
            if os.path.exists(major_path):
                logger.debug('Directory: {} already exists. It will be deleted.'.format(major_path))
                shutil.rmtree(major_path)
            
            os.makedirs(major_path)
            logger.debug('Create directory: {}'.format(major_path))
            
            for course in self.resource_dict[major]:
                
                if self.resource_dict[major][course]['readme_path'] is None:
                    md_path = None
                else:
                    md_path = os.path.join(self.base_path, self.resource_dict[major][course]['readme_path'])
                resource_path_list = [os.path.join(self.base_path, single_path) for single_path in self.resource_dict[major][course]['resource_path']]
                
                # =============== 创建单独的markdown文件，传入的路径为绝对路径 =============== 
                self.write_single_md(course_name=course,
                                     md_path=md_path,
                                     resource_path_list=resource_path_list,
                                     target_dir=major_path)
                
        logger.info('Successfully wrote all the markdown file.')
    
    
    def update_yaml(self):
        """   
        自动更新yaml文件
        """
        
        # 自定义专业顺序，之后通过暴力搜索的方式更新yaml
        major_order = ['公共课程', '计算机科学与技术', '人工智能', '数据科学与大数据技术', '物联网工程', '信息安全', '网络空间安全', '软件工程', '选修课程']
        
        ignore_dir_list = ['img']  # 不关注img文件夹中的内容
        docs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'docs')
        
        new_yaml_data = {
            'site_name': 'HIT-FC-OpenCS',
            'theme': 'readthedocs',
            'repo_url': 'https://github.com/HIT-FC-OpenCS/CS_Courses',
            'nav': [
                {'HIT-FC-OpenCS': 'index.md'}
            ]
        }
        for current_major in major_order:
            for major in os.listdir(docs_path):
                if major not in ignore_dir_list and os.path.isdir(os.path.join(docs_path, major)) and major == current_major:
                    
                    major_dict = {major: []}
                    course_file_list = os.listdir(os.path.join(docs_path, major))
                    
                    for course_file in course_file_list:
                        course_name = course_file.split('.')[0]
                        suffix = course_file.split('.')[1]
                        
                        if suffix != 'md':
                            logger.error('File: {} is not a markdown file.'.format(course_file))
                            exit(1)
                        
                        major_dict[major].append({course_name: os.path.join(major, course_file)})
                        logger.debug('construct major_dict: {}'.format(major_dict))
                    
                    new_yaml_data['nav'].append(major_dict)
            
            with open('mkdocs.yml', 'w', encoding='utf-8') as yaml_file:
                yaml.dump(new_yaml_data, yaml_file, default_flow_style=False, allow_unicode=True)
            yaml_file.close()
            
            logger.info('Successfully wrote yaml file.')


if __name__ == '__main__':
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rf = WebsiteUpdater(root_dir)
    rf.get_resource()
    rf.update_docs()
    rf.update_yaml()
