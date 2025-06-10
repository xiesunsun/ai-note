"""
Markdown解析和验证服务
处理Markdown内容的解析、验证和转换
"""

import re
import html
from typing import List, Dict, Any, Optional
try:
    import markdown2
    MARKDOWN2_AVAILABLE = True
except ImportError:
    MARKDOWN2_AVAILABLE = False

from app.schemas.note import MarkdownValidationResult


class MarkdownService:
    """Markdown服务类"""
    
    def __init__(self):
        # 危险的HTML标签和属性
        self.dangerous_tags = {
            'script', 'iframe', 'object', 'embed', 'form', 'input', 
            'button', 'textarea', 'select', 'option', 'meta', 'link'
        }
        
        self.dangerous_attributes = {
            'onclick', 'onload', 'onerror', 'onmouseover', 'onmouseout',
            'onfocus', 'onblur', 'onchange', 'onsubmit', 'javascript:'
        }
        
        # 允许的HTML标签（基本格式化）
        self.allowed_tags = {
            'p', 'br', 'strong', 'b', 'em', 'i', 'u', 'del', 's', 'strike',
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'pre', 'code',
            'ul', 'ol', 'li', 'a', 'img', 'table', 'thead', 'tbody', 'tr', 'td', 'th'
        }
    
    def validate_markdown(self, content: str) -> MarkdownValidationResult:
        """
        验证Markdown内容
        
        Args:
            content: Markdown内容
            
        Returns:
            MarkdownValidationResult: 验证结果
        """
        errors = []
        warnings = []
        html_content = None
        
        try:
            # 基本格式检查
            if not content or not content.strip():
                errors.append("内容不能为空")
                return MarkdownValidationResult(
                    is_valid=False,
                    errors=errors,
                    warnings=warnings
                )
            
            # 长度检查
            if len(content) > 100000:
                errors.append("内容过长，请控制在100KB以内")
            
            # 安全性检查
            security_issues = self._check_security(content)
            if security_issues:
                errors.extend(security_issues)
            
            # 语法检查
            syntax_issues = self._check_syntax(content)
            warnings.extend(syntax_issues)
            
            # 如果没有严重错误，尝试转换为HTML
            if not errors:
                html_content = self._convert_to_html(content)
            
            return MarkdownValidationResult(
                is_valid=len(errors) == 0,
                html_content=html_content,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            errors.append(f"验证过程中发生错误: {str(e)}")
            return MarkdownValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings
            )
    
    def _check_security(self, content: str) -> List[str]:
        """检查安全性问题"""
        issues = []
        
        # 检查危险的HTML标签
        for tag in self.dangerous_tags:
            pattern = rf'<\s*{tag}[^>]*>'
            if re.search(pattern, content, re.IGNORECASE):
                issues.append(f"检测到危险的HTML标签: {tag}")
        
        # 检查危险的属性
        for attr in self.dangerous_attributes:
            pattern = rf'{attr}\s*='
            if re.search(pattern, content, re.IGNORECASE):
                issues.append(f"检测到危险的HTML属性: {attr}")
        
        # 检查潜在的XSS
        xss_patterns = [
            r'javascript\s*:',
            r'data\s*:\s*text/html',
            r'vbscript\s*:',
            r'on\w+\s*=',
        ]
        
        for pattern in xss_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                issues.append("检测到潜在的XSS攻击代码")
                break
        
        return issues
    
    def _check_syntax(self, content: str) -> List[str]:
        """检查Markdown语法问题"""
        warnings = []
        
        # 检查未闭合的代码块
        code_block_count = content.count('```')
        if code_block_count % 2 != 0:
            warnings.append("检测到未闭合的代码块")
        
        # 检查链接格式
        link_pattern = r'\[([^\]]*)\]\(([^)]*)\)'
        links = re.findall(link_pattern, content)
        for text, url in links:
            if not url.strip():
                warnings.append(f"链接'{text}'缺少URL")
            elif not self._is_valid_url(url.strip()):
                warnings.append(f"链接'{text}'的URL格式可能有问题")
        
        # 检查图片格式
        img_pattern = r'!\[([^\]]*)\]\(([^)]*)\)'
        images = re.findall(img_pattern, content)
        for alt, src in images:
            if not src.strip():
                warnings.append(f"图片'{alt}'缺少源地址")
        
        # 检查标题层级
        headers = re.findall(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE)
        if headers:
            levels = [len(h[0]) for h in headers]
            for i in range(1, len(levels)):
                if levels[i] - levels[i-1] > 1:
                    warnings.append("标题层级跳跃过大，建议按顺序使用")
                    break
        
        return warnings
    
    def _is_valid_url(self, url: str) -> bool:
        """检查URL格式是否有效"""
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        # 也允许相对路径
        relative_pattern = re.compile(r'^[./].*$')
        
        return bool(url_pattern.match(url)) or bool(relative_pattern.match(url))
    
    def _convert_to_html(self, content: str) -> str:
        """
        将Markdown转换为HTML
        优先使用markdown2库，如果不可用则使用简化版本
        """
        if MARKDOWN2_AVAILABLE:
            try:
                # 使用markdown2进行转换，启用安全的扩展
                extras = [
                    'fenced-code-blocks',  # 支持```代码块
                    'tables',              # 支持表格
                    'strike',              # 支持删除线
                    'task_list',           # 支持任务列表
                    'code-friendly',       # 代码友好模式
                ]

                html_content = markdown2.markdown(content, extras=extras)

                # 基本的安全过滤
                html_content = self._sanitize_html(html_content)

                return html_content

            except Exception as e:
                print(f"markdown2转换失败，使用简化版本: {e}")
                return self._convert_to_html_simple(content)
        else:
            return self._convert_to_html_simple(content)

    def _convert_to_html_simple(self, content: str) -> str:
        """
        简化版Markdown转HTML转换
        """
        html_content = content

        # 转义HTML特殊字符
        html_content = html.escape(html_content)

        # 处理代码块
        html_content = re.sub(
            r'```(\w+)?\n(.*?)\n```',
            r'<pre><code class="language-\1">\2</code></pre>',
            html_content,
            flags=re.DOTALL
        )

        # 处理行内代码
        html_content = re.sub(r'`([^`]+)`', r'<code>\1</code>', html_content)

        # 处理标题
        for i in range(6, 0, -1):
            pattern = r'^' + '#' * i + r'\s+(.+)$'
            replacement = f'<h{i}>\\1</h{i}>'
            html_content = re.sub(pattern, replacement, html_content, flags=re.MULTILINE)

        # 处理粗体和斜体
        html_content = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', html_content)
        html_content = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', html_content)

        # 处理链接
        html_content = re.sub(
            r'\[([^\]]+)\]\(([^)]+)\)',
            r'<a href="\2">\1</a>',
            html_content
        )

        # 处理图片
        html_content = re.sub(
            r'!\[([^\]]*)\]\(([^)]+)\)',
            r'<img src="\2" alt="\1" />',
            html_content
        )

        # 处理段落
        paragraphs = html_content.split('\n\n')
        html_paragraphs = []
        for p in paragraphs:
            p = p.strip()
            if p and not p.startswith('<'):
                p = f'<p>{p}</p>'
            html_paragraphs.append(p)

        return '\n'.join(html_paragraphs)

    def _sanitize_html(self, html_content: str) -> str:
        """对HTML内容进行安全过滤"""
        # 移除危险的标签
        for tag in self.dangerous_tags:
            pattern = rf'<\s*{tag}[^>]*>.*?<\s*/\s*{tag}\s*>'
            html_content = re.sub(pattern, '', html_content, flags=re.IGNORECASE | re.DOTALL)

            # 移除自闭合标签
            pattern = rf'<\s*{tag}[^>]*/?>'
            html_content = re.sub(pattern, '', html_content, flags=re.IGNORECASE)

        # 移除危险的属性
        for attr in self.dangerous_attributes:
            pattern = rf'\s{attr}\s*=\s*["\'][^"\']*["\']'
            html_content = re.sub(pattern, '', html_content, flags=re.IGNORECASE)

        return html_content
    
    def extract_text_content(self, markdown_content: str) -> str:
        """从Markdown内容中提取纯文本（用于搜索）"""
        # 移除Markdown语法
        text = markdown_content
        
        # 移除代码块
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        
        # 移除行内代码
        text = re.sub(r'`[^`]+`', '', text)
        
        # 移除链接，保留文本
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        
        # 移除图片
        text = re.sub(r'!\[[^\]]*\]\([^)]+\)', '', text)
        
        # 移除标题标记
        text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
        
        # 移除粗体和斜体标记
        text = re.sub(r'\*+([^*]+)\*+', r'\1', text)
        text = re.sub(r'_+([^_]+)_+', r'\1', text)
        
        # 移除其他Markdown语法
        text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)  # 引用
        text = re.sub(r'^[-*+]\s+', '', text, flags=re.MULTILINE)  # 列表
        text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)  # 有序列表
        
        # 清理多余的空白
        text = re.sub(r'\n+', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()


# 创建全局实例
markdown_service = MarkdownService()
