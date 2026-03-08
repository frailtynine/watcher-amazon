import {
  Box,
  Heading,
  Text,
  HStack,
  IconButton,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Tooltip,
} from '@chakra-ui/react';
import { 
  EditIcon,
  DeleteIcon,
  SettingsIcon,
} from '@chakra-ui/icons';
import { FaPlay, FaPause } from 'react-icons/fa';
import type { NewsTask } from '../../types';

interface NewsTaskCardProps {
  task: NewsTask;
  sourcesCount?: number;
  onEdit: (task: NewsTask) => void;
  onDelete: (id: string) => void;
  onToggleActive: (id: string, active: boolean) => void;
}

export const NewsTaskCard = ({
  task,
  sourcesCount = 0,
  onEdit,
  onDelete,
  onToggleActive,
}: NewsTaskCardProps) => {
  return (
    <Box
      p={5}
      shadow="md"
      borderWidth="1px"
      borderRadius="md"
      bg="white"
      _hover={{ shadow: 'lg' }}
      transition="all 0.2s"
    >
      <HStack justify="space-between" mb={3}>
        <HStack spacing={3}>
          <Tooltip label={task.active ? 'Pause task' : 'Resume task'}>
            <IconButton
              aria-label={task.active ? 'Pause' : 'Play'}
              icon={task.active ? <FaPause /> : <FaPlay />}
              colorScheme={task.active ? 'orange' : 'green'}
              size="sm"
              onClick={() => onToggleActive(task.id, !task.active)}
            />
          </Tooltip>
          <Heading size="md">📋 {task.name}</Heading>
        </HStack>
        <Menu>
          <MenuButton
            as={IconButton}
            icon={<SettingsIcon />}
            variant="ghost"
            size="sm"
          />
          <MenuList>
            <MenuItem icon={<EditIcon />} onClick={() => onEdit(task)}>
              Edit
            </MenuItem>
            <MenuItem
              icon={<DeleteIcon />}
              onClick={() => onDelete(task.id)}
              color="red.500"
            >
              Delete
            </MenuItem>
          </MenuList>
        </Menu>
      </HStack>

      <Text color="gray.600" fontSize="sm" mb={3} noOfLines={2}>
        {task.prompt}
      </Text>

      <HStack fontSize="xs" color="gray.500">
        <Text>{sourcesCount} feeds</Text>
        <Text>•</Text>
        <Text>
          Updated {new Date(task.updated_at).toLocaleDateString()}
        </Text>
      </HStack>
    </Box>
  );
};
