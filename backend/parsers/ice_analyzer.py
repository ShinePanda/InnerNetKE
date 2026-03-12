"""
ICE Slice File Analyzer
Parses .ice (Slice) files for ICE RPC framework
"""
import hashlib
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# ICE Slice basic types
SLICE_BASIC_TYPES = {
    "byte", "short", "int", "long", "float", "double", "string", "bool",
    "Object", "Object*", "ObjectPtr"
}

# Metadata patterns
METADATA_PATTERN = re.compile(r'\[([^\]]+)\]')
COMMENT_PATTERN = re.compile(r'/\*\*?\*/|//.*?$', re.MULTILINE)
DOC_COMMENT_PATTERN = re.compile(r'/\*\*\s*(.*?)\s*\*/', re.DOTALL)


class IceEntityType:
    """ICE entity types"""
    MODULE = "module"
    INTERFACE = "interface"
    CLASS = "class"
    STRUCT = "struct"
    ENUM = "enum"
    SEQUENCE = "sequence"
    DICTIONARY = "dictionary"
    CONST = "const"
    EXCEPTION = "exception"
    OPERATION = "operation"
    PARAMETER = "parameter"


@dataclass
class IceParameter:
    """ICE operation parameter"""
    name: str
    type: str
    direction: str  # "in", "out"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "direction": self.direction
        }


@dataclass
class IceOperation:
    """ICE interface operation"""
    name: str
    return_type: str
    parameters: List[IceParameter] = field(default_factory=list)
    exceptions: List[str] = field(default_factory=list)
    is_idempotent: bool = False
    is_nonmutating: bool = False
    doc_comment: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "return_type": self.return_type,
            "parameters": [p.to_dict() for p in self.parameters],
            "exceptions": self.exceptions,
            "is_idempotent": self.is_idempotent,
            "is_nonmutating": self.is_nonmutating,
            "doc_comment": self.doc_comment
        }


@dataclass
class IceDefinition:
    """ICE definition (interface, struct, enum, etc.)"""
    definition_type: str
    name: str
    extends: List[str] = field(default_factory=list)
    members: List[Dict[str, Any]] = field(default_factory=list)
    operations: List[IceOperation] = field(default_factory=list)
    doc_comment: Optional[str] = None
    metadata: List[str] = field(default_factory=list)
    line_number: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.definition_type,
            "name": self.name,
            "extends": self.extends,
            "members": self.members,
            "operations": [op.to_dict() for op in self.operations],
            "doc_comment": self.doc_comment,
            "metadata": self.metadata,
            "line_number": self.line_number
        }


@dataclass
class IceModule:
    """ICE module"""
    name: str
    definitions: List[IceDefinition] = field(default_factory=list)
    sub_modules: List['IceModule'] = field(default_factory=list)
    line_number: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": IceEntityType.MODULE,
            "name": self.name,
            "definitions": [d.to_dict() for d in self.definitions],
            "sub_modules": [m.to_dict() for m in self.sub_modules],
            "line_number": self.line_number
        }


class IceParser:
    """ICE Slice file parser"""
    
    def __init__(self):
        self.content: str = ""
        self.file_path: str = ""
        self.includes: List[str] = []
        self.modules: List[IceModule] = []
        
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """Parse an ICE file"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        self.file_path = file_path
        self.content = path.read_text(encoding="utf-8")
        
        # Extract includes first
        self._extract_includes()
        
        # Extract modules
        self._extract_modules()
        
        return self.get_result()
    
    def parse_content(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Parse ICE content from string"""
        self.file_path = file_path
        self.content = content
        
        self._extract_includes()
        self._extract_modules()
        
        return self.get_result()
    
    def _extract_includes(self) -> None:
        """Extract #include statements"""
        include_pattern = re.compile(r'#include\s+[<"]([^>"]+)[>"]')
        self.includes = include_pattern.findall(self.content)
    
    def _extract_modules(self) -> None:
        """Extract all module definitions"""
        # Pattern to match module blocks
        module_pattern = re.compile(
            r'module\s+(\w+)\s*\{(.*?)\};',
            re.DOTALL | re.MULTILINE
        )
        
        for match in module_pattern.finditer(self.content):
            module_name = match.group(1)
            module_body = match.group(2)
            line_number = self.content[:match.start()].count('\n') + 1
            
            module = IceModule(
                name=module_name,
                line_number=line_number
            )
            
            # Parse definitions within the module
            module.definitions = self._parse_module_body(module_body, module_name)
            
            self.modules.append(module)
    
    def _parse_module_body(self, body: str, module_name: str) -> List[IceDefinition]:
        """Parse definitions inside a module"""
        definitions = []
        
        # Remove comments for parsing
        clean_body = COMMENT_PATTERN.sub('', body)
        
        # Parse interfaces
        definitions.extend(self._parse_interfaces(clean_body, module_name))
        
        # Parse structs
        definitions.extend(self._parse_structs(clean_body, module_name))
        
        # Parse enums
        definitions.extend(self._parse_enums(clean_body, module_name))
        
        # Parse sequences
        definitions.extend(self._parse_sequences(clean_body, module_name))
        
        # Parse dictionaries
        definitions.extend(self._parse_dictionaries(clean_body, module_name))
        
        # Parse exceptions
        definitions.extend(self._parse_exceptions(clean_body, module_name))
        
        # Parse constants
        definitions.extend(self._parse_constants(clean_body, module_name))
        
        return definitions
    
    def _parse_interfaces(self, body: str, module_name: str) -> List[IceDefinition]:
        """Parse interface definitions"""
        definitions = []
        
        # Match interface with optional extends
        interface_pattern = re.compile(
            r'interface\s+(\w+)(?:\s+extends\s+([^{]+))?\s*\{(.*?)\};',
            re.DOTALL
        )
        
        for match in interface_pattern.finditer(body):
            name = match.group(1)
            extends_str = match.group(2) or ""
            interface_body = match.group(3)
            
            extends = [e.strip() for e in extends_str.split(',') if e.strip()]
            
            # Get line number from original content
            line_number = body[:match.start()].count('\n') + 1
            
            definition = IceDefinition(
                definition_type=IceEntityType.INTERFACE,
                name=name,
                extends=extends,
                line_number=line_number
            )
            
            # Parse operations
            definition.operations = self._parse_operations(interface_body)
            
            definitions.append(definition)
        
        return definitions
    
    def _parse_operations(self, body: str) -> List[IceOperation]:
        """Parse interface operations"""
        operations = []
        
        # Remove comments
        clean_body = COMMENT_PATTERN.sub('', body)
        
        # Operation pattern: ReturnType operationName(params) throws ...;
        op_pattern = re.compile(
            r'(?:(\w+)\s+)?'  # Optional return type
            r'(\w+)\s*'       # Operation name
            r'\(([^)]*)\)'    # Parameters
            r'(?:\s+throws\s+([^{]+))?'  # Optional exceptions
            r'\s*;',
            re.MULTILINE
        )
        
        for match in op_pattern.finditer(clean_body):
            return_type = match.group(1) or "void"
            op_name = match.group(2)
            params_str = match.group(3) or ""
            throws_str = match.group(4) or ""
            
            # Check for idempotent and nonmutating
            is_idempotent = "idempotent" in clean_body[match.start():match.start()+50]
            is_nonmutating = "nonmutating" in clean_body[match.start():match.start()+50]
            
            # Parse parameters
            parameters = self._parse_parameters(params_str)
            
            # Parse exceptions
            exceptions = [e.strip() for e in throws_str.split(',') if e.strip()]
            
            operations.append(IceOperation(
                name=op_name,
                return_type=return_type,
                parameters=parameters,
                exceptions=exceptions,
                is_idempotent=is_idempotent,
                is_nonmutating=is_nonmutating
            ))
        
        return operations
    
    def _parse_parameters(self, params_str: str) -> List[IceParameter]:
        """Parse operation parameters"""
        parameters = []
        
        if not params_str.strip():
            return parameters
        
        # Split by comma, but handle nested brackets
        params = []
        depth = 0
        current = ""
        
        for char in params_str:
            if char in '(<[':
                depth += 1
            elif char in ')>]':
                depth -= 1
            
            if char == ',' and depth == 0:
                params.append(current.strip())
                current = ""
            else:
                current += char
        
        if current.strip():
            params.append(current.strip())
        
        for param in params:
            param = param.strip()
            if not param:
                continue
            
            # Check direction
            direction = "in"
            if param.startswith("out "):
                direction = "out"
                param = param[4:].strip()
            elif param.startswith("in "):
                param = param[3:].strip()
            
            # Parse type and name (last word is name)
            parts = param.split()
            if len(parts) >= 2:
                param_type = " ".join(parts[:-1])
                param_name = parts[-1]
            else:
                param_type = parts[0]
                param_name = "unknown"
            
            parameters.append(IceParameter(
                name=param_name,
                type=param_type,
                direction=direction
            ))
        
        return parameters
    
    def _parse_structs(self, body: str, module_name: str) -> List[IceDefinition]:
        """Parse struct definitions"""
        definitions = []
        
        struct_pattern = re.compile(
            r'struct\s+(\w+)\s*\{(.*?)\};',
            re.DOTALL
        )
        
        for match in struct_pattern.finditer(body):
            name = match.group(1)
            struct_body = match.group(2)
            line_number = body[:match.start()].count('\n') + 1
            
            # Parse members
            members = []
            for line in struct_body.split(';'):
                line = line.strip()
                if not line or line.startswith('//'):
                    continue
                
                parts = line.split()
                if len(parts) >= 2:
                    member_type = " ".join(parts[:-1])
                    member_name = parts[-1]
                    members.append({
                        "type": member_type,
                        "name": member_name
                    })
            
            definitions.append(IceDefinition(
                definition_type=IceEntityType.STRUCT,
                name=name,
                members=members,
                line_number=line_number
            ))
        
        return definitions
    
    def _parse_enums(self, body: str, module_name: str) -> List[IceDefinition]:
        """Parse enum definitions"""
        definitions = []
        
        enum_pattern = re.compile(
            r'enum\s+(\w+)\s*\{(.*?)\};',
            re.DOTALL
        )
        
        for match in enum_pattern.finditer(body):
            name = match.group(1)
            enum_body = match.group(2)
            line_number = body[:match.start()].count('\n') + 1
            
            # Parse enumerators
            members = []
            for member in enum_body.split(','):
                member = member.strip()
                if member:
                    # Handle assigned values like RED = 1
                    member_name = member.split('=')[0].strip()
                    members.append({"name": member_name})
            
            definitions.append(IceDefinition(
                definition_type=IceEntityType.ENUM,
                name=name,
                members=members,
                line_number=line_number
            ))
        
        return definitions
    
    def _parse_sequences(self, body: str, module_name: str) -> List[IceDefinition]:
        """Parse sequence definitions"""
        definitions = []
        
        sequence_pattern = re.compile(
            r'sequence<([^>]+)>\s+(\w+)\s*;'
        )
        
        for match in sequence_pattern.finditer(body):
            element_type = match.group(1)
            name = match.group(2)
            line_number = body[:match.start()].count('\n') + 1
            
            definitions.append(IceDefinition(
                definition_type=IceEntityType.SEQUENCE,
                name=name,
                members=[{"element_type": element_type}],
                line_number=line_number
            ))
        
        return definitions
    
    def _parse_dictionaries(self, body: str, module_name: str) -> List[IceDefinition]:
        """Parse dictionary definitions"""
        definitions = []
        
        dict_pattern = re.compile(
            r'dictionary<([^,]+),\s*([^>]+)>\s+(\w+)\s*;'
        )
        
        for match in dict_pattern.finditer(body):
            key_type = match.group(1)
            value_type = match.group(2)
            name = match.group(3)
            line_number = body[:match.start()].count('\n') + 1
            
            definitions.append(IceDefinition(
                definition_type=IceEntityType.DICTIONARY,
                name=name,
                members=[{"key_type": key_type, "value_type": value_type}],
                line_number=line_number
            ))
        
        return definitions
    
    def _parse_exceptions(self, body: str, module_name: str) -> List[IceDefinition]:
        """Parse exception definitions"""
        definitions = []
        
        exception_pattern = re.compile(
            r'exception\s+(\w+)\s*\{(.*?)\};',
            re.DOTALL
        )
        
        for match in exception_pattern.finditer(body):
            name = match.group(1)
            exception_body = match.group(2)
            line_number = body[:match.start()].count('\n') + 1
            
            # Parse members
            members = []
            for line in exception_body.split(';'):
                line = line.strip()
                if not line or line.startswith('//'):
                    continue
                
                parts = line.split()
                if len(parts) >= 2:
                    member_type = " ".join(parts[:-1])
                    member_name = parts[-1]
                    members.append({
                        "type": member_type,
                        "name": member_name
                    })
            
            definitions.append(IceDefinition(
                definition_type=IceEntityType.EXCEPTION,
                name=name,
                members=members,
                line_number=line_number
            ))
        
        return definitions
    
    def _parse_constants(self, body: str, module_name: str) -> List[IceDefinition]:
        """Parse constant definitions"""
        definitions = []
        
        const_pattern = re.compile(
            r'const\s+(\w+)\s+(\w+)\s*=\s*([^;]+);'
        )
        
        for match in const_pattern.finditer(body):
            const_type = match.group(1)
            const_name = match.group(2)
            const_value = match.group(3).strip()
            line_number = body[:match.start()].count('\n') + 1
            
            definitions.append(IceDefinition(
                definition_type=IceEntityType.CONST,
                name=const_name,
                members=[{"type": const_type, "value": const_value}],
                line_number=line_number
            ))
        
        return definitions
    
    def get_result(self) -> Dict[str, Any]:
        """Get parsed result as dictionary"""
        return {
            "language": "ice",
            "file_path": self.file_path,
            "includes": self.includes,
            "modules": [m.to_dict() for m in self.modules]
        }


class IceAnalyzer:
    """ICE Slice code analyzer"""
    
    def __init__(self):
        self.parser = IceParser()
        self.entity_counter = 0
    
    def analyze_file(self, file_path: str, content: Optional[str] = None) -> Dict[str, Any]:
        """Analyze an ICE file"""
        if content:
            result = self.parser.parse_content(content, file_path)
        else:
            result = self.parser.parse_file(file_path)
        
        # Add analysis results
        result["summary"] = self._generate_summary(result)
        
        return result
    
    def _generate_summary(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary statistics"""
        summary = {
            "module_count": len(result.get("modules", [])),
            "interface_count": 0,
            "struct_count": 0,
            "enum_count": 0,
            "operation_count": 0,
            "exception_count": 0
        }
        
        for module in result.get("modules", []):
            for definition in module.get("definitions", []):
                def_type = definition.get("type")
                
                if def_type == IceEntityType.INTERFACE:
                    summary["interface_count"] += 1
                    summary["operation_count"] += len(definition.get("operations",[]))
                elif def_type == IceEntityType.STRUCT:
                    summary["struct_count"] += 1
                elif def_type == IceEntityType.ENUM:
                    summary["enum_count"] += 1
                elif def_type == IceEntityType.EXCEPTION:
                    summary["exception_count"] += 1
        
        return summary
    
    def generate_entity_id(self, file_path: str, entity_name: str, line: int) -> str:
        """Generate unique entity ID"""
        unique_str = f"{file_path}:{entity_name}:{line}"
        return hashlib.md5(unique_str.encode()).hexdigest()[:16]
